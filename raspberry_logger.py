# Carrega as bibliotecas
import Adafruit_DHT
# import RPi.GPIO as GPIO
import vcgencmd
from gpiozero import CPUTemperature, RGBLED
from time import sleep, time, strftime
import datetime as dt
import matplotlib.pyplot as plt
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import RPi.GPIO as GPIO

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-b_t color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0


# Load default font.
font = ImageFont.load_default()

# see csv on shell: cat sensor_logs.csv

led = RGBLED(red=10, green=9, blue=11)

cpu = CPUTemperature()

sensor = Adafruit_DHT.DHT11

# Define a GPIO conectada ao pino de dados do sensor temperatura e humidade do ar
pin_DHT11 = 25

# Define a GPIO conectada ao pino de dados do sensor temperatura e humidade da terra
pin_soil = 21
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_soil, GPIO.IN)

# Informacoes iniciais
print("*** Lendo os valores de temp de cpu, temp e umidade do ambiente")

plt.ion()
t = []
y_temp_cpu = []
y_temp_env = []
y_umid_env = []
y_soil = []

def write_sensor(temp_cpu, temp_env, umid_env, soil):
    with open("/home/fox17/dev/sensor_logs.csv", "a") as log:
        led.color = (1, 0, 1)  # green
        sleep(0.25)
        led.color = (1, 1, 1)  # off
        log.write("{0},{1},{2},{3},{4}\n".format(strftime("%Y-%m-%d %H:%M:%S"), str(temp_cpu), str(temp_env), str(umid_env), str(soil)))

def graph(temp_cpu, temp_env, umid_env, soil):
    y_temp_cpu.append(temp_cpu)
    y_temp_env.append(temp_env)
    y_umid_env.append(umid_env)
    y_soil.append(soil)
    t.append(dt.datetime.fromtimestamp(time()))
    plt.clf()
    plt.scatter(t, y_temp_cpu)
    plt.scatter(t, y_temp_env)
    plt.scatter(t, y_umid_env)
    plt.scatter(t, y_soil)
    plt.plot_date(t, y_temp_cpu, label="cpu temp")
    plt.plot_date(t, y_temp_env, label="ambiente temp")
    plt.plot_date(t, y_umid_env, label="ambiente umidade")
    plt.plot_date(t, y_soil, label="sensor da terra")
    plt.xlabel("Data")
    plt.ylabel("Sensores")
    plt.gcf().autofmt_xdate
    plt.legend()
    plt.draw()

def screen(umid, temp_env):
    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Shell scripts for system monitoring from here : https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell=True)
    cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
    CPU = subprocess.check_output(cmd, shell=True)
    cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
    MemUsage = subprocess.check_output(cmd, shell=True)
    cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
    Disk = subprocess.check_output(cmd, shell=True)
    cmd = "vcgencmd measure_temp |cut -f 2 -d '='"
    temp = subprocess.check_output(cmd, shell=True)
    cmd = "umid |cut -f 2 -d '='"

    # Write two lines of text.

    draw.text((x, top+2), "IP:" + str(IP, 'utf-8'), font=font, fill=255)
    draw.text((x, top+16), str(CPU, 'utf-8') + " " + str(temp, 'utf-8'), font=font, fill=255)
    draw.text((x, top+27), str(MemUsage, 'utf-8'), font=font, fill=255)
    draw.text((x, top+39), str(Disk, 'utf-8'), font=font, fill=255)
    draw.text((x, top+51), "umid:" + str(umid) + " t_env:" + str(temp_env), font=font, fill=255)

    # Display image.
    disp.image(image)
    disp.display()

while True:
    # Efetua a leitura do sensor
    soil = GPIO.input(pin_soil)
    umid, temp = Adafruit_DHT.read_retry(sensor, pin_DHT11)
    # Caso leitura esteja ok, mostra os valores na tela
    if umid is not None and temp is not None:
        print("Temperatura = {0:0.1f}  Umidade = {1:0.1f}  Solo = {2}".format(temp, umid, soil))
        print("Aguarda 5 segundos para efetuar nova leitura...")
    else:
        # Mensagem de erro de comunicacao com o sensor
        print("Falha ao ler dados do DHT11 !!!")
    temp_cpu = cpu.temperature
    write_sensor(temp_cpu, temp, umid, soil)
    graph(temp_cpu, temp, umid, soil)  # If you want to see a graph, then just uncomment the graph(temp) line using Mu and run the file.
    screen(umid, temp)
    plt.pause(5)

