import numpy as np
from PIL import Image, ImageDraw
import os
import random

def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_abstract_pest(image_size, pest_type):
    image = Image.new('RGB', (image_size, image_size), color='white')
    draw = ImageDraw.Draw(image)
    
    if pest_type == 'aphid':
        # Green oval
        draw.ellipse([20, 20, image_size-20, image_size-20], fill='green')
    elif pest_type == 'whitefly':
        # White triangle
        draw.polygon([(image_size//2, 20), (20, image_size-20), (image_size-20, image_size-20)], fill='lightgrey')
    elif pest_type == 'spider_mite':
        # Red circle with legs
        draw.ellipse([30, 30, image_size-30, image_size-30], fill='red')
        for _ in range(8):  # 8 legs
            angle = random.uniform(0, 2*np.pi)
            x = image_size//2 + int(np.cos(angle) * image_size//3)
            y = image_size//2 + int(np.sin(angle) * image_size//3)
            draw.line([(image_size//2, image_size//2), (x, y)], fill='black', width=2)
    elif pest_type == 'thrips':
        # Brown rectangle
        draw.rectangle([20, 20, image_size-20, image_size-20], fill='brown')
    
    return image

def generate_dataset(base_dir, num_images_per_class=100, image_size=150):
    pest_types = ['aphid', 'whitefly', 'spider_mite', 'thrips']
    
    for split in ['train', 'validation']:
        for pest_type in pest_types:
            directory = os.path.join(base_dir, split, pest_type)
            create_directory(directory)
            
            for i in range(num_images_per_class):
                image = generate_abstract_pest(image_size, pest_type)
                image.save(os.path.join(directory, f"{pest_type}_{i+1}.png"))

    print(f"Generated {num_images_per_class * len(pest_types)} images for each of train and validation sets.")

if __name__ == "__main__":
    base_dir = 'abstract_pest_images'
    generate_dataset(base_dir)
    print(f"Dataset generated in {base_dir}")