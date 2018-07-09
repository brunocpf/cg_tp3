import math

class Vector(object):

    def __init__(self, x, y, z, h=1.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.h = float(h)

    def values(self):
        return (self.x, self.y, self.z, self.h)

    def magnitude(self):
        return math.sqrt(sum(i**2 for i in list(self.values())))

    def normalized(self):
        magnitude = self.magnitude()
        return Vector(*(value / magnitude for value in list(self.values())))

    def dot(self, v2):
        return sum(a * b for a, b in zip(self.values(), v2.values()))

    def cross(self, v2):
        return Vector(self.y * v2.z - self.z * v2.y,
                      self.z * v2.x - self.x * v2.z,
                      self.x * v2.y - self.y * v2.x, 0.0)

    def reflect(self, normal):
        c = (-1.0 * normal).dot(self)
        return (self + (2 * normal * c)).normalized()

    def refract(self, normal, ior):
        c = (-1.0 * normal).dot(self)
        return (ior * self + (ior * c - math.sqrt(1.0 - ior**2.0 * (1.0 - c**2.0))) * normal).normalized()

    def __mul__(self, v2):
        if isinstance(v2, Vector):
            return self.dot(v2)
        else:
            return Vector(*(a * v2 for a in list(self.values())))

    def __rmul__(self, v2):
        return self.__mul__(v2)

    def __truediv__(self, v2):
        if isinstance(v2, Vector):
            return Vector(*(a / b for a, b in zip(self.values(), v2.values())))
        else:
            return Vector(*(a / v2 for a in list(self.values())))

    def __rdiv__(self, v2):
        return self.__div__(v2)

    def __add__(self, v2):
        if isinstance(v2, Vector):
            return Vector(*(a + b for a, b in zip(self.values(), v2.values())))
        else:
            return Vector(*(a + v2 for a in list(self.values())))

    def __radd__(self, v2):
        return self.__add__(v2)

    def __sub__(self, v2):
        return Vector(*(a - b for a, b in zip(self.values(), v2.values())))


class Plane(object):

    def __init__(self, a, b, c, d):
        self.normal = Vector(a, b, c, 0.0).normalized()
        i = next(x for x in [0, 1, 2] if [a, b, c, d][x] != 0)
        if i == 0:
            self.p = Vector(d / a, 0.0, 0.0)
        elif i == 1:
            self.p = Vector(0.0, d / b, 0.0)
        elif i == 2:
            self.p = Vector(0.0, 0.0, d / c)
        self.coefficients = [a, b, c, d]


class Color(Vector):

    def __init__(self, r, g, b, a=1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def values(self):
        return (self.r, self.g, self.b, self.a)

    def clamped(self):
        return Color(
            clamp(0.0, self.r, 1.0),
            clamp(0.0, self.g, 1.0),
            clamp(0.0, self.b, 1.0),
            clamp(0.0, self.a, 1.0)
        )

    def __mul__(self, v2):
        if isinstance(v2, Color):
            return Color(*(a * b for a, b in zip(self.values(), v2.values())))
        else:
            return Color(*(a * v2 for a in list(self.values())))

    def __rmul__(self, v2):
        return self.__mul__(v2)

    def __truediv__(self, v2):
        if isinstance(v2, Color):
            return Color(*(a / b for a, b in zip(self.values(), v2.values())))
        else:
            return Color(*(a / v2 for a in list(self.values())))

    def __add__(self, v2):
        if isinstance(v2, Color):
            return Color(*(a + b for a, b in zip(self.values(), v2.values())))
        else:
            return Color(*(a + v2 for a in list(self.values())))

    def __radd__(self, v2):
        return self.__add__(v2)

    def __sub__(self, v2):
        return Color(*(a - b for a, b in zip(self.values(), v2.values())))


class WorldObject(object):

    def __init__(self, texture, material):
        self.texture = texture
        self.material = material

    @staticmethod
    def parse_obj_params(param_string, textures, materials, it):
        params = param_string.split()
        texture_id = int(params[0])
        material_id = int(params[1])

        surface = params[2]

        if surface == "sphere":
            position = Vector(*list(map(float, params[3:6])))
            radius = float(params[6])
            return SphereObject(textures[texture_id], materials[material_id], position, radius)
        elif surface == "polyhedron":
            plane_count = int(params[3])
            planes = []
            for _ in range(plane_count):
                planes.append(Plane(*list(map(float, next(it).split()))))
            return PolyhedronObject(textures[texture_id], materials[material_id], planes)
        else:
            raise EnvironmentError()


class SphereObject(WorldObject):

    def __init__(self, texture, material, position, radius):
        super().__init__(texture, material)
        self.position = position
        self.radius = radius

    def get_uv(self, position, normal):
        uv = [0.0, 0.0]
        uv[0] = (1.0 + math.atan2(normal.z, normal.x) / math.pi) * 0.5
        uv[1] = math.acos(normal.y) / math.pi
        return uv

    def intersect(self, ray):
        ray_src, ray_dir = ray
        radius_squared = self.radius ** 2.0
        l = self.position - ray_src
        tca = l.dot(ray_dir)
        if tca < 0:
            return False
        d = l.dot(l) - tca ** 2
        if d > radius_squared or radius_squared - 2.0 < 0.0:
            return False
        thc = math.sqrt(radius_squared - 2.0)

        solutions = [tca - thc, tca + thc]

        inv = 1.0
        inside = False

        if solutions[0] < 0 and solutions[1] >= 0 or solutions[0] >= 0 and solutions[1] < 0:
            inv = -1.0
            inside = True

        if solutions[0] < solutions[1]:
            if solutions[0] >= 0:
                return solutions[0], inv * self.get_normal(ray_src + solutions[0] * ray_dir), inside
            elif solutions[1] >= 0:
                return solutions[1], inv * self.get_normal(ray_src + solutions[1] * ray_dir), inside
        else:
            if solutions[1] >= 0:
                return solutions[1], inv * self.get_normal(ray_src + solutions[1] * ray_dir), inside
            elif solutions[0] >= 0:
                return solutions[0], inv * self.get_normal(ray_src + solutions[0] * ray_dir), inside
        return False
    
    def get_normal(self, pos):
        return (pos - self.position).normalized()



class PolyhedronObject(WorldObject):

    def __init__(self, texture, material, planes):
        super().__init__(texture, material)
        self.planes = planes

    def intersect(self, ray):
        ray_src, ray_dir = ray
        min_dist = math.inf
        max_dist = 0.0

        for plane in self.planes:
            d2 = ray_dir.dot(plane.normal)
            #d1 = (plane.p - ray_src).dot(plane.normal)
            
            d1 = (ray_src - Vector(0.0, 0.0, 0.0)).dot(plane.normal) + plane.coefficients[3]
            if -1e-6 <= d2 <= 1e-6:
                if d1 > 1e-6:
                    min_dist = -1.0
            else:
                dist = -d1 / d2
                if d2 > 1e-6:
                    if dist < min_dist:
                        min_dist = dist
                        normal_min = plane.normal
                if d2 < -1e-6:
                    if dist > max_dist:
                        max_dist = dist
                        normal_max = plane.normal

        if min_dist < max_dist:
            return False
        
        if abs(max_dist) <= 1e-6 and min_dist < math.inf:
            return min_dist, -1.0 * normal_min, False
        
        if max_dist > 1e-6:
            return max_dist, normal_max, False

        return False

        for plane in self.planes:
            prod = ray_dir.dot(plane.normal)
            if abs(prod) > 1e-6:
                dist = (plane.p - ray_src).dot(plane.normal) / prod
                if dist < 0:
                    return False
                elif dist < min_dist:
                    min_dist = dist
                    normal = plane.normal

        #print("found poly\n")
        # return False
        return (min_dist, normal) if min_dist is not math.inf else False


class Texture(object):

    @staticmethod
    def parse_text_params(param_string, it):
        params = param_string.split()
        texture_type = params[0]

        if texture_type == "solid":
            color = Color(*list(map(float, params[1:4])))
            return TextSolid(color)
        elif texture_type == "checker":
            color_1 = Color(*list(map(float, params[1:4])))
            color_2 = Color(*list(map(float, params[4:7])))
            return TextChecker(color_1, color_2, float(params[7]))
        elif texture_type == "texmap":
            textfile = params[1]
            p0 = Vector(*list(map(float, next(it).split())))
            p1 = Vector(*list(map(float, next(it).split())))
            text = TextMap(textfile, p0, p1)
            text.base_color = Color(0.9, 0.0, 0.0)
            return text


class TextSolid(Texture):

    def __init__(self, base_color):
        self.base_color = base_color

    def get_color(self, pos, normal):
        return self.base_color


class TextChecker(Texture):

    def __init__(self, color_1, color_2, pattern_size):
        self.color_1 = color_1
        self.color_2 = color_2
        self.pattern_size = pattern_size

    def get_color(self, pos, normal):
        pattern = int(pos.x / self.pattern_size) + int(pos.y /
                                                       self.pattern_size) + int(pos.z / self.pattern_size)
        return self.color_1 if pattern % 2 == 0 else self.color_2


class TextMap(Texture):

    def __init__(self, textfile, p0, p1):
        self.colormap = None# import_ppm(textfile)
        self.p0 = p0
        self.p1 = p1

    def get_color(self, pos, normal):
        return self.base_color


class Material(object):

    def __init__(self, ka, kd, ks, a, kr, kt, ior):
        self.ka = ka
        self.kd = kd
        self.ks = ks
        self.a = a
        self.kr = kr
        self.kt = kt
        self.ior = ior

    @staticmethod
    def parse_material_params(param_string):
        params = param_string.split()
        ka = float(params[0])
        kd = float(params[1])
        ks = float(params[2])
        a = float(params[3])
        kr = float(params[4])
        kt = float(params[5])
        ior = float(params[6])
        return Material(ka, kd, ks, a, kr, kt, ior)


def clamp(minimum, x, maximum):
    if x < minimum:
        return minimum
    elif x > maximum:
        return maximum
    else:
        return x
