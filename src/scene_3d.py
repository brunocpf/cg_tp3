import string
import array
import itertools
import timeit
from tqdm import tqdm
from math import inf
from multiprocessing import Pool
from geometry import *

DEBUG_MODE = False  # whether to run with a process pool or not
MAX_DEPTH = 300  # max reflection recursions


class Scene(object):

    def __init__(self, camera, ambient_light, lights, objects):
        self.camera = camera
        self.ambient_light = ambient_light
        self.lights = lights
        self.objects = objects

    def render_image(self, width, height):
        print("Rendering...")

        image_data = {}

        aspect_ratio = float(width) / float(height)

        d = (self.camera.position - self.camera.proj_position).magnitude()
        plane_down = -1.0 * self.camera.normal
        plane_right = self.camera.direction().cross(self.camera.normal).normalized()
        plane_height = 2 * math.tan(math.radians(0.5 * self.camera.fovy)) * d
        plane_width = plane_height * aspect_ratio
        self.y_transform = plane_height * plane_down * (1.0 / float(height))
        self.x_transform = plane_width * plane_right * (1.0 / float(width))
        self.top_left = self.camera.proj_position + \
            (self.camera.normal * (plane_height / 2.0)) - \
            (plane_right * (plane_width / 2.0))
        image_coords = itertools.product(range(width), range(height))


        if DEBUG_MODE:
            image_data = list(map(self.__shade_pixel__, image_coords))
        else:
            with Pool(4) as p:
                image_data = p.map(self.__shade_pixel__, image_coords)

        return image_data

    def __shade_pixel__(self, screen_position):
        x, y = float(screen_position[0]), float(screen_position[1])
        pixel_position = self.top_left + x * self.x_transform + y * self.y_transform
        ray_dir = (pixel_position - self.camera.position).normalized()
        pixel_color = self.__raytrace__(
            self.camera.position, ray_dir, MAX_DEPTH)
        return (screen_position, (int(pixel_color.r * 255), int(pixel_color.g * 255), int(pixel_color.b * 255)))

    def __cast_ray__(self, src, ray_dir, ignore_obj=None):
        intersection = None
        min_dist = inf
        for obj in self.objects:
            if obj is ignore_obj:
                continue
            # primary ray
            intersection_hit = obj.intersect((src, ray_dir))
            if intersection_hit is not False and intersection_hit[0] < min_dist:
                # obj, dist, normal
                intersection = obj, intersection_hit[0], intersection_hit[1], intersection_hit[2]
                min_dist = intersection_hit[0]
        return intersection

    def __raytrace__(self, src, ray_dir, depth, ignore_obj=None):

        # primary ray
        intersection = self.__cast_ray__(src, ray_dir, ignore_obj)
        if intersection is None:
            return self.ambient_light.color

        obj, dist, normal, inside = intersection
        pos = src + dist * ray_dir

        ambient = self.ambient_light.color * obj.material.ka
        diffuse = Color(0.0, 0.0, 0.0)
        specular = Color(0.0, 0.0, 0.0)
        reflection = Color(0.0, 0.0, 0.0)
        refraction = Color(0.0, 0.0, 0.0)
        final_color = ambient

        for light in self.lights:
            light_vec = (light.position - pos)
            light_dir = light_vec.normalized()
            light_dist = light_vec.magnitude()
            shadowray_intersection = self.__cast_ray__(pos, light_dir)
            if shadowray_intersection is None:
                attenuation = 1.0 / \
                    (light.att_const + light.att_lin *
                     light_dist + (light.att_quad**2) * light_dist)
                diffuse_coeff = max([0.0, light_dir.dot(normal)])
                diffuse = diffuse + light.color * attenuation * diffuse_coeff * obj.material.kd

                specular_coeff = max(
                    [0.0, (light_dir + (-1.0 * ray_dir)).normalized().dot(normal)])
                specular = specular + light.color * attenuation * \
                    (specular_coeff ** obj.material.a) * obj.material.ks

        if depth > 0:
            if obj.material.kr > 0.0:
                reflection_dir = ray_dir.reflect(normal)
                reflection = self.__raytrace__(pos, reflection_dir, depth-1, obj) * obj.material.kr
            if obj.material.kt > 0.0:
                coeff = (1.0/obj.material.kt) if inside else (obj.material.kt)
                refraction_dir = ray_dir.refract(normal, obj.material.ior)
                refraction = self.__raytrace__(pos, refraction_dir, depth-1, obj) * coeff

        final_color = obj.texture.get_color(pos, normal) * (ambient + diffuse) + specular + reflection + refraction
        return final_color.clamped()


class Camera(object):

    def __init__(self, position, proj_position, normal, fovy):
        self.position = position
        self.proj_position = proj_position
        self.normal = normal
        self.fovy = fovy

    def direction(self):
        return (self.position - self.proj_position).normalized()

    @staticmethod
    def parse_camera_data(it):
        position = Vector(*list(map(float, next(it).split())))
        proj_position = Vector(*list(map(float, next(it).split())))
        normal = Vector(*list(map(float, next(it).split())), 0.0).normalized()
        fovy = float(next(it))
        return Camera(position, proj_position, normal, fovy)


class Light(object):

    def __init__(self, position, color, att_const, att_lin, att_quad):
        self.position = position
        self.color = color
        self.att_const = att_const
        self.att_lin = att_lin
        self.att_quad = att_quad

    @staticmethod
    def parse_light_params(param_string):
        params = param_string.split()
        position = Vector(*list(map(float, params[0:3])))
        color = Color(*list(map(float, params[3:6])))
        att_const = float(params[6])
        att_lin = float(params[7])
        att_quad = float(params[7])
        return Light(position, color, att_const, att_lin, att_quad)


def parse_input_data(input_filename):
    print("Parsing input data...")

    with open(input_filename) as fd:
        lines = fd.read().splitlines()
    it = (i for i in lines)

    camera = Camera.parse_camera_data(it)

    lights_count = int(next(it))
    ambient_light = Light.parse_light_params(next(it))
    lights = []
    for _ in range(lights_count - 1):
        lights.append(Light.parse_light_params(next(it)))

    textures_count = int(next(it))
    textures = []
    for _ in range(textures_count):
        textures.append(Texture.parse_text_params(next(it), it))

    materials_count = int(next(it))
    materials = []
    for _ in range(materials_count):
        materials.append(Material.parse_material_params(next(it)))

    obj_count = int(next(it))
    objs = []
    for _ in range(obj_count):
        objs.append(WorldObject.parse_obj_params(
            next(it), textures, materials, it))

    return camera, ambient_light, lights, objs
