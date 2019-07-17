import pygame, sys, math
from pygame.locals import *
from Vector2D import Vec2D

pygame.init()

width, height = 1280, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Ray Casting")

pygame.mouse.set_visible(False)
pygame.event.set_grab(True)

surf_width, surf_height = int(width / 2), height

colours = {
    'background': (50, 50, 50),
    'particle': (255, 255, 255),
    'ray': (120, 140, 120),
    'segment': (255, 120, 0),
    'light': (200, 200, 200),
    'boundary': (255, 120, 0)
}

class Particle:
    def __init__(self, pos):
        self.pos = pos
        self.fov = math.pi / 3
        self.angle = 0
        self.colour = colours['particle']
        self.radius = 4
        self.moving = False
        self.moving_dir = []

    def cast(self):
        self.rays = []
        angle_per_ray = self.fov / num_rays
        for i in range(num_rays):
            start_angle = self.angle - self.fov / 2
            self.rays.append(Ray(self.pos, start_angle + i * angle_per_ray))

    def calcDists(self):
        dist_list = []
        angle_per_ray = self.fov / num_rays
        for i in range(num_rays):
            dist = self.pos.distTo(self.points[i])
            ## Correct fish-eye effect
            angle = self.fov / 2 - i * angle_per_ray
            perp_dist = math.cos(angle) * dist
            dist_list.append(perp_dist)
        return dist_list

    def update(self, mouse_movement, walls):
        ## Set viewing angle to determine FOV range, also for first person movement
        self.angle += mouse_movement.x * mouse_sensitivity / 100 ## Arbitrary 100
        self.dir = Vec2D(math.cos(self.angle), math.sin(self.angle)).normalise()

        ## Moving the particle
        for dir in self.moving_dir:
            if dir == 'w':
                d_pos = self.dir
            elif dir == 'a':
                d_pos = self.dir.perpendicular()
            elif dir == 's':
                d_pos = self.dir * -1
            elif dir == 'd':
                d_pos = self.dir.perpendicular() * -1
            else: d_pos = Vec2D(0, 0)
            new_pos = self.pos + d_pos * particle_speed
            if self.radius < new_pos.x < surf_width - boundary_width - self.radius and self.radius < new_pos.y < surf_height - boundary_width - self.radius:  ## If in screen
                if surf_2D.get_at((new_pos + (d_pos * self.radius)).tuple()) == colours['background']:
                    self.pos = new_pos

        self.cast()

        self.points = []
        for ray in self.rays:
            self.points.append(ray.update(walls))
            if draw_rays:
                ray.show() ## Draw each ray
        self.points.append(self.pos) ## Closing off polygon with self.pos

    def show(self):
        ## Drawing light
        if draw_light:
            pygame.draw.polygon(surf_2D, colours['light'], [point.tuple() for point in self.points])  ## Filled light
        else:
            pygame.draw.polygon(surf_2D, colours['light'], [point.tuple() for point in self.points], 2) ## Draw outline
        ## Drawing particle
        pygame.draw.circle(surf_2D, self.colour, self.pos.tuple(), self.radius)

class Ray:

    colour = colours['ray']

    def __init__(self, start_pos, angle):
        self.start_pos = start_pos
        self.end_pos = None
        self.angle = angle
        self.dir = Vec2D(math.cos(self.angle), math.sin(self.angle))

    def intersect(self, p1, p2):
        den = (p1.x - p2.x) * (self.start_pos.y - (self.start_pos.y + self.dir.y)) - (p1.y - p2.y) * (self.start_pos.x - (self.start_pos.x + self.dir.x))

        if den == 0:
            return

        t = ((p1.x - self.start_pos.x) * (self.start_pos.y - (self.start_pos.y + self.dir.y)) - (p1.y - self.start_pos.y) * (self.start_pos.x - (self.start_pos.x + self.dir.x))) / den
        u = -(((p1.x - p2.x) * (p1.y - self.start_pos.y) - (p1.y - p2.y) * (p1.x - self.start_pos.x)) / den)

        if t > 0 and t < 1 and u > 0:
            x = p1.x + t * (p2.x - p1.x)
            y = p1.y + t * (p2.y - p1.y)
            return Vec2D(x, y)
        else:
            return None

    def update(self, walls):
        ## Each update the ray looks for the closest intersection from its position towards its angle
        closest_dist = math.inf
        closest_point = None

        for wall in walls:
            point = self.intersect(wall.p1, wall.p2)
            if point:
                dist = self.start_pos.sqrDistTo(point) ## Square of dist to save processing
                if dist < closest_dist:
                    closest_dist = dist
                    closest_point = point
        ## Closest point is guaranteed as there is a bounding box present
        if closest_point is None: raise AttributeError('No intersections found - BUG')
        self.end_pos = closest_point
        return closest_point

    def show(self):
        pygame.draw.line(surf_2D, self.colour, self.start_pos.tuple(), self.end_pos.tuple())

## 'Wall' segment
class Segment:
    def __init__(self, p1, p2):
        self.p1, self.p2 = p1, p2

    def intersect(self, seg):
        den = (seg.p1.x - seg.p2.x) * (self.p1.y - self.p2.y) - (seg.p1.y - seg.p2.y) * (self.p1.x - self.p2.x)

        if den == 0:
            return

        t = ((seg.p1.x - self.p1.x) * (self.p1.y - self.p2.y) - (seg.p1.y - self.p1.y) * (self.p1.x - self.p2.x)) / den
        u = -(((seg.p1.x - seg.p2.x) * (seg.p1.y - self.p1.y) - (seg.p1.y - seg.p2.y) * (seg.p1.x - self.p1.x)) / den)

        if t >= 0 and t <= 1 and u >= 0 and u <= 1:
            x = seg.p1.x + t * (seg.p2.x - seg.p1.x)
            y = seg.p1.y + t * (seg.p2.y - seg.p1.y)
            return Vec2D(x, y)
        else:
            return

    def show(self):
        pygame.draw.line(surf_2D, colours['segment'], self.p1.tuple(), self.p2.tuple())

## Shape class designed for shapes with sides that do not intersect
class Shape:
    def __init__(self, sides, colour, points, fill=True):
        if sides != len(points): raise IndexError("Invalid length of point list")
        self.sides = sides
        self.points = points
        self.segments = [Segment(self.points[i], self.points[(i + 1) % self.sides]) for i in range(self.sides)]
        self.colour = colour
        self.width = 0 if fill else particle_speed

    def show(self):
        pygame.draw.polygon(surf_2D, self.colour, [point.tuple() for point in self.points], self.width)

## Get relative mouse position as a Vector2D obj
def getRelMousePos():
    rel_mouse_pos = Vec2D(*pygame.mouse.get_rel())
    return rel_mouse_pos

def map(val, in_min, in_max, out_min, out_max):
    return out_min + ((out_max - out_min) / (in_max - in_min) * (val - in_min))

def render3D(dist_list):
    line_width = surf_width / num_rays
    for i in range(num_rays):
        if dist_list[i] <= render_dist:
            # line_height = map(dist_list[i], 0, render_dist, surf_height, 0) # farthest_dist / dist_list[i] ## Calculate each lines height relative to the ray's distance
            line_height = farthest_dist / dist_list[i] * 50 ## Arbitrary constant
            rect = pygame.Rect(i * line_width, surf_height / 2 - line_height / 2, line_width, line_height)
            colour = map(dist_list[i], 0, render_dist, 255, 0) ## Calculate colour based on distance, eg. farther away, darker
            pygame.draw.rect(surf_3D, [colour] * 3, rect)

# CONSTANTS
boundary_width = 2 ## Width of the boundary lines
draw_rays = True ## Draw individual rays
draw_light = False ## Draw light polygon
num_rays = 80 ## Number of rays to be cast, eg. 10 16 20 32 40 64 80 128 160 320 640
farthest_dist = math.sqrt(surf_width ** 2 + surf_height ** 2) ## Calculate farthest possible distance for render3D()
render_dist = farthest_dist ## Maximum distance for rendering
mouse_sensitivity = 0.4 ## Self-explanatory
particle_speed = 4 ## Number of pixels travelled per frame by Particle

def setup():
    global finished, particle, segments, shapes, surf_2D, surf_3D
    finished = False

    ## Particle(starting_pos)
    particle = Particle(Vec2D(100, 300))

    ## Custom shapes
    shapes = [
        ## Bounding box
        Shape(4, colours['boundary'], [Vec2D(0, 0), Vec2D(surf_width - boundary_width, 0), Vec2D(surf_width - boundary_width, surf_height - boundary_width), Vec2D(0, surf_height - boundary_width)], fill=False),
        ## Test shapes
        Shape(8, (120, 255, 255), [Vec2D(358, 108), Vec2D(282, 108), Vec2D(228, 162), Vec2D(228, 238), Vec2D(282, 292), Vec2D(358, 292), Vec2D(412, 238), Vec2D(412, 162)]),
        Shape(6, (120, 255, 255), [Vec2D(50, 50), Vec2D(50, 150), Vec2D(85, 150), Vec2D(85, 100), Vec2D(120, 100), Vec2D(120, 50)]),
        Shape(5, (120, 255, 255), [Vec2D(500, 240), Vec2D(443, 281), Vec2D(465, 349), Vec2D(535, 349), Vec2D(557, 281)])
    ]

    segments = []
    for shape in shapes:
        for side in shape.segments:
            segments.append(side)

    surf_2D = pygame.Surface((surf_width, surf_height))
    surf_3D = pygame.Surface((surf_width, surf_height))

setup()

while True:
    if not finished:
        surf_2D.fill(colours['background'])
        surf_3D.fill(colours['background'])

    for event in pygame.event.get():
        if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        ## Detecting WASD inputs for moving particle
        if event.type == pygame.KEYDOWN:
            if chr(event.key) in ['w', 'a', 's', 'd']:
                particle.moving = True
                particle.moving_dir.append(chr(event.key))
            ## Reset
            elif chr(event.key) == 'r':
                setup()
        ## Stop moving
        elif event.type == pygame.KEYUP:
            if chr(event.key) in ['w', 'a', 's', 'd']:
                particle.moving = False
                try:
                    particle.moving_dir.remove(chr(event.key))
                except ValueError: pass ## To catch error when resetting while still moving

    for shape in shapes:
        shape.show()

    particle.update(getRelMousePos(), segments)
    particle.show()

    dists = particle.calcDists()
    render3D(dists)

    screen.blit(surf_2D, (0, 0))
    screen.blit(surf_3D, (surf_width, 0))

    pygame.display.update()
