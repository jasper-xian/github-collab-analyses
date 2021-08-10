from io import BytesIO
import matplotlib.pyplot as plt
import random
def generate_random_color():
    red = random.random() * 255
    green = random.random() * 255
    blue = random.random() * 255
    red = int((red + 197.472) / 2)
    green = int((green + 178.347) / 2)
    blue = int((blue + 197.472) / 2)
    return '#%02x%02x%02x' % (red, green, blue)

def generateDonutPieChart(scores):
    labels = []
    sizes = []
    colors = []
    for item in scores:
        labels.append(item[0])
        sizes.append(item[1])
        colors.append(generate_random_color())

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, colors = colors, labels=labels, autopct='%1.1f%%', startangle=90)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    ax1.axis('equal')  
    plt.tight_layout()
    img = BytesIO()
    plt.savefig(img)
    img.seek(0)
    return img