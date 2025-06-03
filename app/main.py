from display import Display
import time

disp = Display()

disp.clear()
disp.draw_square(5, 5, 10,   (255, 0, 0))
disp.draw_circle(45, 30, 10, (0, 255, 0))


disp.overlay_set_color( (0,0,50) )
disp.overlay_set_type( 1 )

disp.overlay_square(25, 25, 5)
disp.overlay_circle(32, 32, 8)

disp.show()
time.sleep(5)
