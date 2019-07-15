import pygame, sys, math, random
from pygame.locals import *
from Vector2D import Vec2D

pygame.init()

width, height = 1280, 400
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Ray Casting")

surf_width, surf_height = width / 2, height

colours = {
    'background': (50, 50, 50),
    'particle': (255, 255, 255),
    'ray': (120, 140, 120),
    'segment': (255, 120, 0),
    'light': (200, 200, 200),
    'boundary': (255, 120, 0)
}

particle_speed = 4
directions = {
    'w': Vec2D(0, -particle_speed),
    'a': Vec2D(-particle_speed, 0),
    's': Vec2D(0, particle_speed),
    'd': Vec2D(particle_speed, 0)
}

class Particle:
    def __init__(self, pos):
        self.pos = pos
        self.fov = math.pi / 2
        self.colour = colours['particle']
        self.size = 8
        self.moving = False
        self.moving_dir = []

    def cast(self):
        self.rays = []
        for i in range(num_rays):
            start_angle = self.angle - self.fov / 2
            self.rays.append(Ray(self.pos, start_angle + i * (self.fov / num_rays)))

    def calcDists(self):
        dist_list = []
        for i in range(num_rays):
            dist = self.pos.distTo(self.points[i])
            dist_list.append(dist)
        return dist_list

    def update(self, lookingAt, walls):
        ## Moving the particle
        for dir in self.moving_dir:
            new_pos = self.pos + directions[dir]
            if 0 < new_pos.x < surf_width and 0 < new_pos.y < surf_height: ## If in screen
                self.pos = new_pos

        ## Set viewing angle to determine FOV range
        self.angle = self.pos.angleTo(lookingAt)
        self.dir = lookingAt - self.pos

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
        pygame.draw.circle(surf_2D, self.colour, self.pos.tuple(), int(self.size / 2))

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
                dist = self.start_pos.distTo(point)
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
    def __init__(self, sides, colour, points, width=0):
        if sides != len(points): raise IndexError("Invalid length of point list")
        self.sides = sides
        self.points = points
        self.segments = [Segment(self.points[i], self.points[(i + 1) % self.sides]) for i in range(self.sides)]
        self.colour = colour
        self.width = width

    def show(self):
        pygame.draw.polygon(surf_2D, self.colour, [point.tuple() for point in self.points], self.width)

def getMousePos():
    ## Converting mouse position to a 2D Vector
    mouse_pos = Vec2D(*pygame.mouse.get_pos())
    return mouse_pos

def render3D(dist_list):
    pixel_width = surf_width / num_rays
    for i in range(num_rays):
        pixel_height = 2000 / dist_list[i]
        rect = pygame.Rect(i * pixel_width, surf_height / 2 - pixel_height / 2, pixel_width, pixel_height)
        pygame.draw.rect(surf_3D, (255, 255, 255), rect)

# CONSTANTS
eps = 0.00001 ## Very small number
boundary_width = 2 ## Width of the boundary lines
draw_rays = True ## Draw individual rays
draw_light = False ## Draw light polygon
num_rays = 100

def setup():
    global finished, particle, segments, shapes, surf_2D, surf_3D
    finished = False

    ## Particle(starting_pos)
    particle = Particle(Vec2D(surf_width / 2, surf_height / 2))

    segments = []
    ## Random walls
    for i in range(5):
        p1 = Vec2D(random.randint(0, surf_width), random.randint(0, surf_height))
        p2 = Vec2D(random.randint(0, surf_width), random.randint(0, surf_height))
        segments.append(Segment(p1, p2))

    ## Custom shapes
    shapes = [
        ## Bounding box
        Shape(4, colours['boundary'], [Vec2D(0, 0), Vec2D(surf_width - boundary_width, 0), Vec2D(surf_width - boundary_width, surf_height - boundary_width), Vec2D(0, surf_height - boundary_width)], boundary_width),
        ## Test octagon
        Shape(8, (120, 255, 255), [Vec2D(358, 108), Vec2D(282, 108), Vec2D(228, 162), Vec2D(228, 238), Vec2D(282, 292), Vec2D(358, 292), Vec2D(412, 238), Vec2D(412, 162)], 2)
    ]

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
            if chr(event.key) in directions.keys():
                particle.moving = True
                particle.moving_dir.append(chr(event.key))
            ## Reset
            elif chr(event.key) == 'r':
                setup()
        ## Stop moving
        elif event.type == pygame.KEYUP:
            if chr(event.key) in directions.keys():
                particle.moving = False
                try:
                    particle.moving_dir.remove(chr(event.key))
                except ValueError: pass ## To catch error when resetting while still moving

    particle.update(getMousePos(), segments)
    particle.show()

    dists = particle.calcDists()
    render3D(dists)

    for segment in segments:
        segment.show()

    for shape in shapes:
        shape.show()

    screen.blit(surf_2D, (0, 0))
    screen.blit(surf_3D, (surf_width, 0))

    pygame.display.update()
