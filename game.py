from ursina.prefabs.health_bar import HealthBar
from ursina import *
from ursina import invoke
import random


def update():
    global offset, factor, score, score_display, bonus

    # offset speed factor and fuel, nitro and slo-mo usage

    fuel_bar.value -= time.dt
    if held_keys['w'] and nitro_bar.value > 0:
        factor += 0.01
        fuel_bar.value -= time.dt
        nitro_bar.value -= time.dt * 20
        if factor > 1.5:
            factor = 1.5
    elif held_keys['s'] and slow_mo_bar.value > 0:
        factor -= 0.01
        fuel_bar.value += time.dt * 0.25
        slow_mo_bar.value -= time.dt * 20
        if factor < 0.75:
            factor = 0.75
    else:
        factor = 1

    if fuel_bar.value <= 0:
        application.pause()
        Text(text="Out of fuel! Reload the game",
             origin=(0, 0),
             scale=2,
             color=color.yellow,
             background=True)

    fuel_bar.value = round(fuel_bar.value, 2)
    slow_mo_bar.value = round(slow_mo_bar.value, 2)

    offset += time.dt * 0.3 * factor
    setattr(track, "texture_offset", (0, offset))

    # score update
    score += 0.016666666 * factor * bonus
    score_display.text = "Score: {}".format(round(score))

    # turning car
    car0.x += held_keys['d'] * time.dt * 0.3
    car0.x -= held_keys['a'] * time.dt * 0.3

    car0.rotation_y = 0
    if held_keys['a']:
        car0.rotation_y = -0.5
    if held_keys['d']:
        car0.rotation_y = 0.5

    for refill in fuels:
        refill.z -= time.dt * 0.3 * factor
        if car0.intersects(refill).hit:
            fuel_bar.value += 10
            fuels.remove(refill)
            destroy(refill)
        elif refill.z < -2:
            fuels.remove(refill)
            destroy(refill)

    for car in cars:
        if car.rotation_y == 0:  # cars
            car.z -= time.dt * random.uniform(0.05, 0.07) * factor
        else:  # cars180
            car.z -= time.dt * random.uniform(0.2, 0.4) * factor

        # my_car boundary check
        if car0.z < -0.1:
            car0.z = -0.1
        if car0.z > 0.38:
            car0.z = 0.38
        if car0.x >= 0.35:
            car0.x = 0.35
        if car0.x <= -0.35:
            car0.x = -0.35

        # collision check & damage
        if car0.intersects(car).hit:
            damage_bar.value -= 2
            display_crash()
            if (abs(car0.z - car.z) > 0.005) and (car0.z < car.z) and (car.rotation_y == 180):
                car.z += 0.01
            elif (abs(car0.z - car.z) > 0.005) and (car0.z < car.z):
                car.z += 0.0025
            elif (abs(car0.z - car.z) < 1) and (car0.x < car.x):
                car0.x -= 0.005
            elif (abs(car0.z - car.z) < 1) and (car0.x > car.x):
                car0.x += 0.005
            # crashed car
            if damage_bar.value == 0:
                application.pause()
                Text(text="Totalled!"
                          " Your score is: "
                          + str(int(score)) + ". "
                          + "Reload the game.",
                     origin=(0, 0),
                     scale=2,
                     color=color.yellow,
                     background=True)

        # bottom boundary check
        if car.z < -1:
            cars.remove(car)
            destroy(car)

    # collision check between traffic cars
    for i in range(len(cars)):
        for j in range(i + 1, len(cars)):
            if cars[i].intersects(cars[j]).hit:
                if cars[j].rotation_y == 180:
                    cars[j].z += 0.01
                else:
                    cars[j].z += 0.005

    # bonus points for driving wrong way
    if car0.x < 0:
        bonus = 1.5
    else:
        bonus = 1


def new_car180():
    new = Car(0.12, car_positions[0:2])
    cars.append(new)
    invoke(new_car180, delay=random.uniform(0.4, 0.8))


def new_car():
    new = Car(0.12, car_positions[2:4])
    cars.append(new)
    invoke(new_car, delay=random.uniform(1, 3))


def nitro_slow_mo_refill():
    nitro_bar.value += 1
    slow_mo_bar.value += 1
    invoke(nitro_slow_mo_refill, delay=0.5)


def fuel_refill():
    new = FuelRefill(car_positions)
    fuels.append(new)
    invoke(fuel_refill, delay=10)


app = Ursina()

# Start function

start_game = Entity(ignore_paused=True)
start_text = Text("Try to beat my score of 84.\n"
                  "Wrong-way driving grants x1.5 score multiplier.\n"
                  "Grab fuel for a refill.\n"
                  "Nitro and slow motion refills automatically.\n"
                  "Game ends when health goes to 0.\n"
                  "Controls: A/D=Turning, W=Nitro and S=Slo mo.\n"
                  "Press Enter to start.",
                  origin=(-0.5, 0),
                  scale=2,
                  enabled=True,
                  color=color.yellow,
                  background=True)

start_text.x -= 0.5
start_text.background.x -= 0.275

application.paused = True


def start_game_input(key):
    if key == 'enter' and application.paused:
        application.paused = False
        start_text.enabled = application.paused
        run_functions()


start_game.input = start_game_input


# information bars


class Bar(HealthBar):

    def __init__(self, color, position, scale, text):
        super().__init__()
        self.roundness = 0.5
        self.animation_duration = 0.001
        self.bar_color = color
        self.position = position
        self.scale = scale
        self.show_text = text


damage_bar = Bar(color.red.tint(0.25), (-0.79, 0.45), (0.55, 0.025), True)
fuel_bar = Bar(color.green.tint(0.3), (0.37, 0.45), (0.42, 0.023), False)
nitro_bar = Bar(color.blue.tint(0.25), (0.37, 0.40), (0.42, 0.023), False)
slow_mo_bar = Bar(color.violet.tint(0.25), (0.37, 0.35), (0.42, 0.023), False)

# score

score = 0
score_display = Text(text="Score: {}".format(round(score)),
                     position=(0.69, 0.48))
bonus = 1

# track

track = Entity(model="plane",
               scale=(10, 0.5, 60),
               position=(0, 0),
               texture="assets/track")


# icons

class Icon(Entity):

    def __init__(self, img, scale, position):
        super().__init__()
        self.parent = camera.ui
        self.model = "cube"
        self.texture = img
        self.scale = scale
        self.position = position
        self.ignore_paused = False


icons_img = ["assets/hp", "assets/fuel", "assets/nitro", "assets/slowmo"]

hp = Icon(icons_img[0], 0.04, (-0.82, 0.4375))
fuel = Icon(icons_img[1], (0.03, 0.04), (0.343, 0.44))
nitro = Icon(icons_img[2], (0.025, 0.04), (0.34, 0.389))
slowmo = Icon(icons_img[3], (0.03, 0.04), (0.34, 0.339))

# cars

cars_img = ["assets/car" + str(s) for s in range(6)]
car_positions = [-0.3, -0.1, 0.1, 0.3]
car_scales = {'car0.png': 0.045,
              'car1.png': 0.07,
              'car2.png': 0.045,
              'car3.png': 0.045,
              'car4.png': 0.06,
              'car5.png': 0.08}


class Car(Entity):
    scale_y = 0.0001

    def __init__(self, scale_x, car_position):
        super().__init__()
        self.parent = track
        self.model = "cube"
        self.texture = random.choice(cars_img)
        self.choice = random.choice(car_position)
        self.scale = (scale_x, self.scale_y, car_scales[str(self.texture)])
        self.position = (self.choice, 1, 0.4)
        self.collider = "box"
        if self.choice < 0:
            self.angle = 180
        else:
            self.angle = 0
        self.rotation_y = self.angle
        self.ignore_paused = False


cars = []


class MyCar(Entity):
    def __init__(self):
        super().__init__()
        self.parent = track
        self.model = "cube"
        self.texture = "assets/my_car"
        self.scale = (0.12, 0.0001, 0.045)
        self.position = (0.1, 1, -0.12)
        self.collider = "box"
        self.rotation_y = 0
        self.ignore_paused = False


car0 = MyCar()


# fuel_refill


class FuelRefill(Entity):
    def __init__(self, car_position):
        super().__init__()
        self.parent = track
        self.model = "cube"
        self.texture = icons_img[1]
        self.scale = (0.1, 0.1, 0.03)
        self.choice = random.choice(car_position)
        self.position = (self.choice, 1, 2)
        self.collider = "box"
        self.ignore_paused = False


fuels = []
fuel_refill()


def run_functions():
    if not application.paused:
        new_car180()
        new_car()
        nitro_slow_mo_refill()


# crash

crash_entity = Entity(model="plane",
                      parent=track,
                      texture=None,
                      scale=(0.2, 0.04, 0.04),
                      position=(0, -100, 0))
crash_texture = load_texture("assets/crash")


def display_crash():
    crash_entity.texture = crash_texture
    crash_entity.position = (car0.position + (0, 0.1, 0))
    invoke(set_texture_none, delay=0.25)


def set_texture_none():
    crash_entity.texture = None
    crash_entity.position = (0, -100, 0)


# view

factor = 1

offset = 0

camera.position = (0, 35, -33)
camera.rotation_x = 45

app.run()
