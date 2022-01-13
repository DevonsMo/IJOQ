# Version 0.1.1 (Updated 1/12/2021)
# Made by Devons Mo

from PIL import Image, ImageDraw
import random
import math
import csv

probabilities = [0, 0.1, 0.2, 0.3, 0.5, 0.7]
image_count = 10
dampener = 0.6
intersection_count = 10
image_size = 512

cell_size = image_size / (intersection_count - 2)
length_array = []

for k in range(image_count * len(probabilities)):
    probability = probabilities[math.floor(k / image_count)]
    intersections = [[[0] * 2 for i in range(intersection_count)] for j in range(intersection_count)]

    # Determine intersection positions
    for i in range(intersection_count):
        for j in range(intersection_count):
            intersections[i][j][0] = round((i + dampener * (random.random() - 0.5) - 0.5) * cell_size)
            intersections[i][j][1] = round((j + dampener * (random.random() - 0.5) - 0.5) * cell_size)

    # Draw lines between points
    length = 0
    image = Image.new("RGB", (image_size, image_size))
    draw = ImageDraw.Draw(image)
    # Draw horizontal lines
    for i in range(intersection_count - 1):
        for j in range(intersection_count):
            # Remove lines
            if random.random() > probability:
                intersection = [intersections[i][j][0], intersections[i][j][1],
                                intersections[i + 1][j][0], intersections[i + 1][j][1]]

                draw.line(intersection, fill=(255, 255, 255), width=4)

                # Add length
                line_length = ((intersection[0] - intersection[2])**2 + (intersection[1] - intersection[3])**2)**0.5
                # On the left
                if i == 0:
                    ratio = intersection[2] / (intersection[2] - intersection[0])
                    length += ratio * line_length
                # On the right
                elif i == intersection_count - 2:
                    ratio = (image_size - intersection[0]) / (intersection[2] - intersection[0])
                    length += ratio * line_length
                # Normal
                else:
                    length += line_length

    # Draw vertical lines
    for i in range(intersection_count):
        for j in range(intersection_count - 1):
            # Remove lines
            if random.random() > probability:
                intersection = [intersections[i][j][0], intersections[i][j][1],
                                intersections[i][j + 1][0], intersections[i][j + 1][1]]

                draw.line(intersection, fill=(255, 255, 255), width=4)

                # Add length
                line_length = ((intersection[0] - intersection[2]) ** 2 + (intersection[1] - intersection[3]) ** 2) ** 0.5
                # On the top
                if j == 0:
                    ratio = intersection[3] / (intersection[3] - intersection[1])
                    length += ratio * line_length
                # On the bottom
                elif j == intersection_count - 2:
                    ratio = (image_size - intersection[1]) / (intersection[3] - intersection[1])
                    length += ratio * line_length
                # Normal
                else:
                    length += line_length

    print(length)
    image.save(str(k + 1) + ".png")
    length_array.append(length)

with open("length.csv", mode="w", newline="") as data_file:
    data_writer = csv.writer(data_file)
    data_writer.writerow(["File name", "Length"])
    for i in range(image_count * len(probabilities)):
        data_writer.writerow([i + 1, length_array[i]])
