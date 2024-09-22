import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import RegularPolygon
import random
import toml
from perlin_noise import PerlinNoise




class HexMap:
    def __init__(self, config, load_from_file=False):
        self.config = config
        self.size = 3
        self.environments = config['environments']
        self.special_locations = config.get('special_locations', [])
        self.environment_colors = {env: color for env, color in self.environments}
        self.history = []  # Stack to keep track of previous states
        
        self.random_events = [
            "You found a treasure chest!",
            "A wild beast attacks you!",
            "You meet a wandering merchant.",
            "You discover a hidden cave.",
            "An old wizard offers you a quest."
            "You find an old battlefield."
        ]
        self.event_hexes = {}

        self.rows = config['rows']
        self.cols = config['cols']
        self.coordinates = self.generate_hex_coordinates(self.rows, self.cols, self.size)
        self.grid = self.generate_hex_grid(self.rows, self.cols)
        self.land_tiles = self.get_land_tiles()  
        

        if not load_from_file and not self.special_locations:
            self.generate_special_locations()

        self.assign_random_events()

        self.fig, self.ax = plt.subplots()
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.plot_hex_grid()

        self.save_to_toml(config.get('filename', 'hex_map_config.toml'))

    def generate_hex_coordinates(self, rows, cols, size):
        if size is None:
            raise ValueError("Hexagon size must be a number, not None")
        coordinates = []
        for row in range(rows):
            for col in range(cols):
                x = size * 3/2 * col
                y = size * np.sqrt(3) * (row + 0.5 * (col % 2))
                coordinates.append((x, y))
        return coordinates

    def generate_hex_grid(self, rows, cols):
        elevation_noise = PerlinNoise(octaves=4, seed=random.randint(0, 1000))
        moisture_noise = PerlinNoise(octaves=4, seed=random.randint(0, 1000))
    
        environment_rules = {
            'ocean': {'elevation': (0, 0.3), 'moisture': (0, 1)},
            'lake': {'elevation': (0, 0.3), 'moisture': (0.5, 1)},
            'beach': {'elevation': (0.3, 0.45), 'moisture': (0, 0.5)},
            'plains': {'elevation': (0.3, 0.45), 'moisture': (0.5, 1)},
            'grassland': {'elevation': (0.45, 0.6), 'moisture': (0, 0.5)},
            'forest': {'elevation': (0.45, 0.6), 'moisture': (0.5, 1)},
            'desert': {'elevation': (0.6, 0.75), 'moisture': (0, 0.5)},
            'dry plains': {'elevation': (0.6, 0.75), 'moisture': (0.5, 1)},
            'mountain': {'elevation': (0.75, 1), 'moisture': (0, 0.4)},
            'highlands': {'elevation': (0.75, 1), 'moisture': (0.4, 1)}
        }
    
        
        active_rules = {env: rule for env, rule in environment_rules.items() if env in self.environment_colors}
    
        grid = []
        for row in range(rows):
            grid_row = []
            for col in range(cols):
                elevation = (elevation_noise([col / cols, row / rows]) + 1) / 2
                moisture = (moisture_noise([col / cols, row / rows]) + 1) / 2
    
                
                best_match = None
                min_diff = float('inf')
                for env, rule in active_rules.items():
                    if rule['elevation'][0] <= elevation < rule['elevation'][1] and \
                            rule['moisture'][0] <= moisture < rule['moisture'][1]:
                        best_match = env
                        break
                    else:
                        
                        diff = abs(elevation - (rule['elevation'][0] + rule['elevation'][1]) / 2) + \
                               abs(moisture - (rule['moisture'][0] + rule['moisture'][1]) / 2)
                        if diff < min_diff:
                            min_diff = diff
                            best_match = env
    
                
                grid_row.append(best_match)
            grid.append(grid_row)
    
        return grid
    

    def get_land_tiles(self):
        
        land_tiles = []
        water_types = ['ocean', 'lakes', 'lake','oceans']  
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] not in water_types:
                    land_tiles.append((row, col))
        return land_tiles

    def generate_special_locations(self):
        
        special_types = ['dungeon', 'wizard tower', 'village']
        num_special_locations = min(len(self.land_tiles), len(special_types))

        random.shuffle(self.land_tiles)  
        for i in range(num_special_locations):
            location = self.land_tiles.pop()  
            special_location = {
                'type': special_types[i],
                'row': location[0],
                'col': location[1]
            }
            self.special_locations.append(special_location)


    def plot_hex_grid(self):
        if self.size is None:
            raise ValueError("Hexagon size must be a number, not None")
        self.ax.clear()
        coordinates = self.generate_hex_coordinates(self.rows, self.cols, self.size)
        for i, (x, y) in enumerate(coordinates):
            row = i // self.cols
            col = i % self.cols
            environment = self.grid[row][col]
            color = self.environment_colors[environment]
            hexagon = RegularPolygon((x, y), numVertices=6, radius=self.size,
                                     orientation=np.radians(30), edgecolor='black', facecolor=color)
            self.ax.add_patch(hexagon)

        # Plot special locations
        for loc in self.special_locations:
            loc_x = loc['col'] * self.size * 3 / 2
            loc_y = loc['row'] * self.size * np.sqrt(3) + (self.size * np.sqrt(3) / 2 if loc['col'] % 2 else 0)
            if loc['type'] == 'dungeon':
                dungeon = RegularPolygon((loc_x, loc_y), numVertices=3, radius=self.size / 3,
                                         orientation=np.radians(30), edgecolor='black', facecolor='black',
                                         label='Dungeon')
                self.ax.add_patch(dungeon)
            elif loc['type'] == 'wizard tower':
                tower = RegularPolygon((loc_x, loc_y), numVertices=3, radius=self.size / 3,
                                       orientation=np.radians(30), edgecolor='black', facecolor='black',
                                       label='Wizard Tower')
                self.ax.add_patch(tower)
            elif loc['type'] == 'village':
                village = RegularPolygon((loc_x, loc_y), numVertices=3, radius=self.size / 3,
                                         orientation=np.radians(30), edgecolor='black', facecolor='brown',
                                         label='Village')
                self.ax.add_patch(village)

        self.ax.set_aspect('equal')
        self.ax.set_xlim(-self.size, self.size * 1.5 * (self.cols + 1))
        self.ax.set_ylim(-self.size, self.size * np.sqrt(3) * (self.rows + 1))
        plt.axis('off')
        plt.draw()

    
    
    def onclick(self, event):
        
        if event.xdata is None or event.ydata is None:
            return  # Ignore clicks outside the plot area

        # If there is already a highlighted hex, do nothing
        if hasattr(self, 'highlighted_hex') and self.highlighted_hex:
            return

        
        coordinates = self.generate_hex_coordinates(self.rows, self.cols, self.size)

        
        closest_hex_center = min(
            coordinates, 
            key=lambda coord: np.hypot(event.xdata - coord[0], event.ydata - coord[1])
        )

        
        self.highlighted_hex = RegularPolygon(
            xy=closest_hex_center,       
            numVertices=6,               
            radius=self.size,            
            orientation=np.radians(30),  
            edgecolor='red',             
            facecolor='none',            
            linewidth=2                  
        )

        
        self.ax.add_patch(self.highlighted_hex)
        self.fig.canvas.draw_idle()

    def assign_random_events(self):
        """Assigns random events to random land hexes."""
        num_events = min(len(self.land_tiles), len(self.random_events)) 
        random.shuffle(self.land_tiles)  
        
        for i in range(num_events):
            location = self.land_tiles.pop()
            event = self.random_events[i]
            self.event_hexes[location] = event

    def move_highlight(self, direction):
        """Move the highlighted hexagon based on the direction (1-6)."""
        if not hasattr(self, 'highlighted_hex'):
            print("No hexagon is highlighted.")
            return
    
        current_center = self.highlighted_hex.xy
        next_center = self.get_neighbor_hex(current_center, direction)
        
        if next_center:
            try:
                
                self.highlighted_hex.remove()
            except ValueError as e:
                print("Error removing the current hexagon:", e)
                return
        
            
            self.highlighted_hex = RegularPolygon(
                xy=next_center,                
                numVertices=6,                 
                radius=self.size,              
                orientation=np.radians(30),    
                edgecolor='red',               
                facecolor='none',              
                linewidth=2                    
            )
            self.ax.add_patch(self.highlighted_hex)

            self.fig.canvas.draw_idle()

            self.check_for_event(next_center)
        else:
            print("Cannot move in that direction.")

    def check_for_event(self, center):
        """Check if the current hex has an event and display it."""
        for (row, col), event in self.event_hexes.items():
            hex_x = col * self.size * 3 / 2
            hex_y = row * self.size * np.sqrt(3) + (self.size * np.sqrt(3) / 2 if col % 2 else 0)
            if np.isclose(center[0], hex_x) and np.isclose(center[1], hex_y):
                print(f"Event: {event}")
                plt.text(center[0], center[1], event, fontsize=12, ha='center', va='center', color='blue', bbox=dict(facecolor='white', alpha=0.8))
                plt.draw()
                break
    
    def get_neighbor_hex(self, center, direction):
        """Get the neighboring hexagon based on the direction for horizontally aligned hexes."""
        x, y = center
        offsets = {
            1: (0, self.size * np.sqrt(3)),                 
            2: (self.size * 1.5, self.size * np.sqrt(3)/2), 
            3: (self.size * 1.5, -self.size * np.sqrt(3)/2),
            4: (0, -self.size * np.sqrt(3)),                
            5: (-self.size * 1.5, -self.size * np.sqrt(3)/2),
            6: (-self.size * 1.5, self.size * np.sqrt(3)/2),
        }
        offset = offsets.get(direction)
        if offset:
            new_center = (x + offset[0], y + offset[1])
            
            if new_center in self.coordinates:
                return new_center
        return None

    def run(self):
        
        while True:
            try:
                direction = int(input("Enter direction (1-6) to move the highlight, or 0 to exit: "))
                if direction == 0:
                    break
                elif direction in range(1, 7):
                    self.move_highlight(direction)
                else:
                    print("Invalid input. Please enter a number between 1 and 6.")
            except ValueError:
                print("Invalid input. Please enter a valid number.")
    
    def load_from_toml(self, filename):
        with open(filename, 'r') as toml_file:
            hex_map_data = toml.load(toml_file)
        print(filename)
        self.rows = hex_map_data['rows']
        self.cols = hex_map_data['cols']
        self.size = hex_map_data['size']
        self.grid = hex_map_data['grid']
        self.environments = hex_map_data['environments']
        self.special_locations = hex_map_data.get('special_locations', [])
        self.environment_colors = {env: color for env, color in self.environments}

        self.plot_hex_grid()
    
    def save_to_toml(self, filename):
        hex_map_data = {
            'rows': self.rows,
            'cols': self.cols,
            'size': self.size,
            'grid': self.grid,
            'environments': self.environments,
            'special_locations': self.special_locations
        }
        with open(filename, 'w') as toml_file:
            toml.dump(hex_map_data, toml_file)

    def update_config(self, new_config):
        self.config.update(new_config)
        self.size = self.config['size']
        self.environments = self.config['environments']
        self.environment_colors = {env: color for env, color in self.environments}
        self.rows = self.config['rows']
        self.cols = self.config['cols']
        self.special_locations = self.config.get('special_locations', [])
        self.grid = self.generate_hex_grid(self.rows, self.cols)
        self.plot_hex_grid()
        self.save_to_toml()


def user_input():
    choice = input("Do you want to load a configuration from a TOML file or create a new one? (load/new): ").strip().lower()
    
    if choice == 'load':
        filename = input("Enter the filename of the TOML file: ").strip()
        try:
            with open(filename, 'r') as toml_file:
                config = toml.load(toml_file)
            return config
        except FileNotFoundError:
            print(f"File {filename} not found. Please try again.")
            return user_input()
    elif choice == 'new':
        rows = int(input("Enter the number of rows: "))
        cols = int(input("Enter the number of columns: "))
        

        env = input("Enter environment names separated by commas (eg: ocean, lake, beach, plains, grassland, forests, ): ").split(',')
        col = input("Enter corresponding colors separated by commas: ").split(',')
        
        environments = list(zip([env.strip() for env in env], [color.strip() for color in col]))

        config = {
            'rows': rows,
            'cols': cols,
            'size': 3,
            'environments': environments,
            'special_locations': []
        }

        save_choice = input("Do you want to save this configuration to a TOML file? (yes/no): ").strip().lower()
        if save_choice == 'yes':
            filename = input("Enter the filename to save as (including .toml extension): ").strip()
            with open(filename, 'w') as toml_file:
                toml.dump(config, toml_file)
            print(f"Configuration saved to {filename}")
        
        return config
    else:
        print("Invalid choice. Please enter 'load' or 'new'.")
        return user_input()

config = user_input()
hex_map = HexMap(config=config)

plt.ion()
plt.show()


while True:
    plt.pause(0.1)  
    try:
        direction = int(input("Enter direction (1-6) to move the highlight, or 0 to exit: "))
        if direction == 0:
            break
        elif direction in range(1, 7):
            hex_map.move_highlight(direction)
        else:
            print("Please enter a number between 1 and 6.")
    except ValueError:
        print("Invalid input, please enter a number.")

