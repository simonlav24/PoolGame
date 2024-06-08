import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# Load and set up the texture
def load_texture(filename):
    try:
        texture_surface = pygame.image.load(filename)
        texture_surface = pygame.transform.flip(texture_surface, True, False)
        texture_data = pygame.image.tostring(texture_surface, "RGB", 1)
        width = texture_surface.get_width()
        height = texture_surface.get_height()

        glEnable(GL_TEXTURE_2D)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    except FileNotFoundError:
        return 0

    return texture_id

def create_spin_texture():

    grid_size = 32
    single_size = 50
    win_size = grid_size * single_size

    # Initialize Pygame and set up the display
    pygame.init()
    display = (win_size, win_size)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)

    # Set up the orthographic projection to map world coordinates to screen coordinates
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, win_size, 0, win_size, -1, 1)  # Orthographic projection
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    def draw_sphere(x, y, i, j, ):
        glPushMatrix()
        glTranslatef(x, y, 0)
        
        glScalef(single_size / 2, single_size / 2, 1)  # Scale sphere to be 32x32 pixels in screen coordinates

        angle = 360.0 / grid_size
        glRotate(angle * i,0,1,0)
        glRotate(angle * j,-1,0,0)

        #glRotate(angle * i,0,1,1)
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)  # Enable texturing for the quadric
        glBindTexture(GL_TEXTURE_2D, texture_id)
        gluSphere(quad, 1, 32, 32)  # Radius is 1 in the local coordinate system
        gluDeleteQuadric(quad)
        glPopMatrix()

    # Main loop
    number = 0
    done = False
    while not done:
        save_image = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    save_image = True
                    
                if event.key == pygame.K_ESCAPE:
                    done = True

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        texture_id = load_texture(f'Assets/ball_{number}.png')

        for i in range(grid_size):
            for j in range(grid_size):
                # Position spheres in a grid with spacing to ensure 32x32 pixel size
                draw_sphere(i * single_size + single_size / 2, j * single_size + single_size / 2, i, j)

        pygame.display.flip()
        pygame.time.wait(10)
        save_image = True
        
        if save_image:
            # Save the rendered image as a PNG file
            pixels = glReadPixels(0, 0, win_size, win_size, GL_RGB, GL_UNSIGNED_BYTE)
            img = pygame.image.fromstring(pixels, (win_size, win_size), 'RGB')
            output = f'Assets/ball_{number - 1}_spin.png'
            pygame.image.save(img, output)
            print(f'Image saved as {output}')
            save_image = False

        number += 1
        if number > 16:
            done = True

    pygame.quit()

if __name__ == '__main__':
    create_spin_texture()