import random as rnd
from ed2d import window
from ed2d import sysevents
from ed2d.events import Events
from ed2d import context
from ed2d import timing
from ed2d import files
from ed2d import shaders
from ed2d.opengl import gl
from ed2d.opengl import pgl
from gem import vector
from gem import matrix
from ed2d import texture
from ed2d import mesh
from ed2d.physics import rectangle
from ed2d.physics import cmodel
from ed2d.physics import physobj
from ed2d.physics import physengine
from ed2d.physics import primitives
from ed2d.physics import gjk
from ed2d.csg import csg
from ed2d import view
from ed2d import text
from ed2d.scenegraph import SceneGraph
from ed2d import audio
from ed2d import cursor

class GameManager(object):
    ''' Entry point into the game, and manages the game in general '''
    def __init__(self):

        self.width = 800
        self.height = 600
        self.title = "ed2d"
        self.running = False

        self.fpsTimer = timing.FpsCounter()
        self.fpsEstimate = 0

        self.sysEvents = sysevents.SystemEvents()
        self.window = window.Window(self.title, self.width, self.height, window.WindowedMode)
        self.context = context.Context(3, 3, 2)
        self.context.window = self.window

        Events.add_listener(self.process_event)

        self.keys = []
        self.mouseButtons = []
        self.mousePosX = 0
        self.mousePosY = 0
        cursor.set_relative_mode(True)
        cursor.show_cursor()

        self.audio = audio.Audio()
        audioPath = files.resolve_path('data', 'sound', 'test.wav')
        self.audioFile = audio.AudioFile(audioPath)
        self.audioFile.play()
        print(self.audioFile.get_pos())
        print(self.audioFile.get_pos())

        gl.init()
        major = pgl.glGetInteger(gl.GL_MAJOR_VERSION)
        minor = pgl.glGetInteger(gl.GL_MINOR_VERSION)
        print('OpenGL Version: {}.{}'.format(major, minor))

        gl.glViewport(0, 0, self.width, self.height)

        # For CSG to work properly
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        vsPath = files.resolve_path('data', 'shaders', 'main.vs')
        fsPath = files.resolve_path('data', 'shaders', 'main.fs')

        vertex = shaders.VertexShader(vsPath)
        fragment = shaders.FragmentShader(fsPath)
        self.program = shaders.ShaderProgram(vertex, fragment)
        self.program.use()

        self.vao = pgl.glGenVertexArrays(1)

        self.scenegraph = SceneGraph()

        # Load character image into new opengl texture
        imagePath = files.resolve_path('data', 'images', 'cubix.png')
        self.texAtlas = texture.Texture(imagePath, self.program)

        # Physics Test Scene
        # Create a physics engine
        self.physicsEngineTest = physengine.PhysEngine()

        # Player
        # Create a rectangle the long way, this will be the player
        self.cModelTestRect = rectangle.Rectangle(100.0, 100.0, width=32.0, height=32.0)
        self.cModelTestRect.update()

        # Creating a object steps:
        # Create a collision model object
        # Create a physics object to simulate
        # Create a mesh object to render
        self.cModelTest = cmodel.cModel(self.cModelTestRect)
        self.physicsObjectTest = physobj.PhysObj(self.cModelTest, vector.Vector(3, data=[0.0, 0.0, 1.0]))
        self.physicsEngineTest.addObject(self.physicsObjectTest)
        self.meshObjectTest = mesh.Mesh()
        playerACSG = csg.CSG().cube([0, 0, 0], [1, 1, 1])
        playerBCSG = csg.CSG().sphere([0, 0, 0], 1.35, 16, 8)
        playerACSG.setColor(0.5, 0.0, 1.0)
        playerBCSG.setColor(1.0, 1.0, 0.0)
        playerFCSG = playerACSG.subtract(playerBCSG) #change to subtract, union, intersect for different outcome
        self.meshObjectTest.fromCSG(playerFCSG)
        self.meshObjectTest.addProgram(self.program)
        self.meshObjectTest.addTexture(None)
        self.meshObjectTest.addPhysicsObject(self.physicsObjectTest)
        self.meshObjectTestID = self.scenegraph.establish(self.meshObjectTest)
        # End Player

        # Scene objects
        # For now store all the mesh objects in here
        # We need some sort of rendering engine class

        print(self.audioFile.get_pos())

        for i in range(20):
            xRND = rnd.randrange(1, (self.width-32))
            yRND = rnd.randrange(1, (self.height-32))
            # The creating object stuff from above... One Liner... Yes I know. :|
            self.physicsEngineTest.addObject(physobj.PhysObj(cmodel.cModel(rectangle.Rectangle(xRND, yRND, width=32.0, height=32.0)), vector.Vector(3, data=[0.0, 0.0, 1.0])))
            tempObj = self.physicsEngineTest.getObject(i+1)
            tempObj.getCollisionModel().getModel().scale(32, 32)
            tempObj.getCollisionModel().getModel().update()
            tempMesh = mesh.Mesh()
            tempMesh.fromData(data=[
             [0.0, 1.0, 0.0],
             [1.0, 1.0, 0.0],
             [0.0, 0.0, 0.0],
             [1.0, 0.0, 0.0]])
            #tempMesh.setColorAll(1.0, 0.0, 0.0)
            tempMesh.addProgram(self.program)
            tempMesh.addTexture(self.texAtlas)
            tempMesh.addPhysicsObject(tempObj)
            self.scenegraph.establish(tempMesh)

        # End Scene Objects



        # Create the collider
        gjkTest = gjk.GJK()

        # Box A and Box B collistion test, should return False
        # Substract the origins and add the two rectangles together to form a bigger one
        # If it include the origin, collision happens
        boxTestA = primitives.Box(vector.Vector(3, data=[50, 50, 49]), 1, 1, 1, matrix.Matrix(4))
        boxTestB = primitives.Box(vector.Vector(3, data=[50, 50, 51]), 2, 2, 2, matrix.Matrix(4))

        # Rectangle A and Rectangle B collision test, should return False
        # Substract the origins and add the two boxes together to form a bigger one
        # If it include the origin, collision happens
        rectTestA = primitives.Rectangle(vector.Vector(3, data=[10, 10, 0]), 2, 2, matrix.Matrix(4))
        rectTestB = primitives.Rectangle(vector.Vector(3, data=[50, 50, 50]), 2, 2, matrix.Matrix(4))

        # Circle A and Cirlce B collision test, should return False
        # Substract the origins and add the radii
        # If the new circle includes the origin, collision happens
        circleTestA = primitives.Circle(vector.Vector(3, data=[50, 50, 50]), 1)
        circleTestB = primitives.Circle(vector.Vector(3, data=[50, 50, 53]), 1)

        print("Box A and Box B collision:", gjkTest.intersects(boxTestA, boxTestB))
        print("Rect A and Rect B collision:", gjkTest.intersects(rectTestA, rectTestB))
        print("Circle A and Circle B collision:", gjkTest.intersects(circleTestA, circleTestB))

        # Circle A and Box/Rect B collision detection, 2D object with a 3D/2D object, it combines the two different shapes
        # If the new shape includes the origin, collision happens
        # Should return true because they are touching, if not interesting each other at a depth
        print("Circle A and Box B collision:", gjkTest.intersects(circleTestA, boxTestB))
        print("Circle A and Rect B collision:", gjkTest.intersects(circleTestA, rectTestB))


        self.view = view.View()
        self.ortho = matrix.orthographic(0.0, self.width, self.height, 0.0, -1.0, 1.0)
        self.view.new_projection('ortho', self.ortho)
        self.view.register_shader('ortho', self.program)

        self.loadText()

        glerr = gl.glGetError()
        if glerr != 0:
            print('GLError:', glerr)

    def loadText(self):
        vsPath = files.resolve_path('data', 'shaders', 'font.vs')
        fsPath = files.resolve_path('data', 'shaders', 'font.fs')

        vertex = shaders.VertexShader(vsPath)
        fragment = shaders.FragmentShader(fsPath)
        self.textProgram = shaders.ShaderProgram(vertex, fragment)

        fontPath = files.resolve_path('data', 'SourceCodePro-Regular.ttf')
        self.font = text.Font(12, fontPath)
        self.text = text.Text(self.textProgram, self.font)

        self.view.register_shader('ortho', self.textProgram)

    def resize(self, width, height):
        self.width = width
        self.height = height
        gl.glViewport(0, 0, self.width, self.height)
        self.ortho = matrix.orthographic(0.0, self.width, self.height, 0.0, -1.0, 1.0)
        self.view.set_projection('ortho', self.ortho)

    def process_event(self, event, data):
        if event == 'quit' or event == 'window_close':
            self.running = False
        elif event == 'window_resized':
            winID, x, y = data
            self.resize(x, y)
        elif event == 'mouse_move':
            print (data)

            if cursor.is_relative():
                xrel, yrel = data
                self.mousePosX += xrel
                self.mousePosY += yrel
            else:
                self.mousePosX, self.mousePosY = data
        elif event == 'key_down':
            if data[0] == 'r':
                cursor.set_relative_mode(True)
            elif data[0] == 'd':
                cursor.set_relative_mode(False)
            self.keys.append(data[0])
            print(self.keys)
        elif event == 'key_up':
            self.keys.remove(data[0])
        elif event == 'mouse_button_down':
            self.mouseButtons.append(data[0])
            print(self.mouseButtons)
        elif event == 'mouse_button_up':
            self.mouseButtons.remove(data[0])

    def update(self):
        self.scenegraph.update()

        # Translate and then update it, this can be handled better but for now, this will do
        self.physicsObjectTest.translate(self.mousePosX, self.mousePosY)

        # Disabled because it can get really annoying, really fast >:[
        # self.physicsEngineTest.simulate(self.fpsTimer.tickDelta)

    def render(self):
        gl.glClearColor(0.5, 0.5, 0.5, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        self.textProgram.use()
        self.text.draw_text(str(self.fpsEstimate) + ' FPS', 0, 10)

        self.program.use()
        gl.glBindVertexArray(self.vao)

        #self.meshObjectTest.render()

        self.scenegraph.render()

        gl.glBindVertexArray(0)

    def do_run(self):
        ''' Process a single loop '''
        self.sysEvents.process()
        self.update()
        self.render()
        self.window.flip()
        self.fpsTimer.tick()

        # print(self.audioFile.get_pos())
        if self.fpsTimer.fpsTime >= 2000:
            self.fpsEstimate = self.fpsTimer.get_fps()
            print("{:.2f} fps".format(self.fpsEstimate))

    def run(self):
        ''' Called from launcher doesnt exit until the game is quit '''
        self.running = True
        while self.running:
            self.do_run()
        self.audioFile.destroy()
        self.audio.destroy()
