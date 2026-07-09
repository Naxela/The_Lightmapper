import bpy, math, os, gpu, importlib
import numpy as np
from . import utility
from fractions import Fraction
from gpu_extras.batch import batch_for_shader

def splitLogLuvAlphaAtlas(imageIn, outDir, quality):
    pass

def splitLogLuvAlpha(imageIn, outDir, quality):
    
    bpy.app.driver_namespace["logman"].append("Starting LogLuv split for: " + str(imageIn))

    cv2 = importlib.util.find_spec("cv2")

    if cv2 is None:
        print("CV2 not found - Ignoring filtering")
        return 0
    else:
        cv2 = importlib.__import__("cv2")

    print(imageIn)
    image = cv2.imread(imageIn, cv2.IMREAD_UNCHANGED)
    split = cv2.split(image)
    merged = cv2.merge([split[0], split[1], split[2]])
    alpha = split[3]
    image_name = os.path.basename(imageIn)[:-4]

    cv2.imwrite(os.path.join(outDir, image_name+"_XYZ.png"), merged)
    cv2.imwrite(os.path.join(outDir, image_name+"_W.png"), alpha)

def encodeLogLuvGPU(image, outDir, quality):

    bpy.app.driver_namespace["logman"].append("Starting LogLuv encode for: " + str(image.name))

    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    width = input_image.size[0]
    height = input_image.size[1]

    offscreen = gpu.types.GPUOffScreen(width, height)

    vertex_shader = '''
        in vec2 texCoord;
        in vec2 pos;
        out vec2 texCoord_interp;

        void main()
        {
            gl_Position = vec4(pos.xy, 0.0, 1.0);
            texCoord_interp = texCoord;
        }
    '''
    
    fragment_shader = '''
        in vec2 texCoord_interp;
        out vec4 fragColor;

        uniform sampler2D image;
        
        const mat3 cLogLuvM = mat3( 0.2209, 0.3390, 0.4184, 0.1138, 0.6780, 0.7319, 0.0102, 0.1130, 0.2969 );
        vec4 LinearToLogLuv( in vec4 value )  {
            vec3 Xp_Y_XYZp = cLogLuvM * value.rgb;
            Xp_Y_XYZp = max( Xp_Y_XYZp, vec3( 1e-6, 1e-6, 1e-6 ) );
            vec4 vResult;
            vResult.xy = Xp_Y_XYZp.xy / Xp_Y_XYZp.z;
            float Le = 2.0 * log2(Xp_Y_XYZp.y) + 127.0;
            vResult.w = fract( Le );
            vResult.z = ( Le - ( floor( vResult.w * 255.0 ) ) / 255.0 ) / 255.0;
            return vResult;
        }
        
        void main()
        {
            fragColor = LinearToLogLuv(texture(image, texCoord_interp));
        }
    '''

    # Full-screen quad in NDC coordinates
    vertices = ((-1, -1), (-1, 1), (1, 1), (1, -1))
    texcoords = ((0, 0), (0, 1), (1, 1), (1, 0))

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = width,
                height = height,
                alpha = True,
                float_buffer = False
                )

    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    batch = batch_for_shader(
        shader, 'TRI_FAN',
        {
            "pos": vertices,
            "texCoord": texcoords,
        },
    )

    # Create GPU texture from image
    gpu_texture = gpu.texture.from_image(input_image)
    
    with offscreen.bind():
        fb = gpu.state.active_framebuffer_get()
        
        shader.bind()
        shader.uniform_sampler("image", gpu_texture)
        batch.draw(shader)
        
        # Read pixels from framebuffer
        pixel_buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')

    offscreen.free()
    
    # Convert buffer to flat list and normalize
    pixel_buffer.dimensions = width * height * 4
    target_image.pixels = [v / 255 for v in pixel_buffer]
    
    #Save LogLuv
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(target_image.name)
    target_image.filepath_raw = outDir + "/" + target_image.name + ".png"
    target_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    target_image.save()


def encodeImageRGBDGPU(image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    width = input_image.size[0]
    height = input_image.size[1]

    offscreen = gpu.types.GPUOffScreen(width, height)

    vertex_shader = '''
        in vec2 texCoord;
        in vec2 pos;
        out vec2 texCoord_interp;

        void main()
        {
            gl_Position = vec4(pos.xy, 0.0, 1.0);
            texCoord_interp = texCoord;
        }
    '''
    
    fragment_shader = '''
        in vec2 texCoord_interp;
        out vec4 fragColor;

        uniform sampler2D image;

        const float LinearEncodePowerApprox = 2.2;
        const float GammaEncodePowerApprox = 1.0 / LinearEncodePowerApprox;
        const float Epsilon = 0.0000001;
        #define saturate(x) clamp(x, 0.0, 1.0)

        float maxEps(float x) {
            return max(x, Epsilon);
        }

        vec3 toGammaSpace(vec3 color)
        {
            return pow(color, vec3(GammaEncodePowerApprox));
        }

        const float rgbdMaxRange = 255.0;

        vec4 toRGBD(vec3 color) {
            float maxRGB = maxEps(max(color.r, max(color.g, color.b)));
            float D      = max(rgbdMaxRange / maxRGB, 1.);
            D            = clamp(floor(D) / 255.0, 0., 1.);
            vec3 rgb = color.rgb * D;
            rgb = toGammaSpace(rgb);
            return vec4(rgb, D); 
        }

        void main()
        {
            fragColor = toRGBD(texture(image, texCoord_interp).rgb);
        }
    '''

    # Full-screen quad in NDC coordinates
    vertices = ((-1, -1), (-1, 1), (1, 1), (1, -1))
    texcoords = ((0, 0), (0, 1), (1, 1), (1, 0))

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    # Removing .exr or .hdr prefix
    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = width,
                height = height,
                alpha = True,
                float_buffer = False
                )

    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    batch = batch_for_shader(
        shader, 'TRI_FAN',
        {
            "pos": vertices,
            "texCoord": texcoords,
        },
    )

    # Create GPU texture from image
    gpu_texture = gpu.texture.from_image(input_image)
    
    with offscreen.bind():
        fb = gpu.state.active_framebuffer_get()
        
        shader.bind()
        shader.uniform_sampler("image", gpu_texture)
        batch.draw(shader)
        
        # Read pixels from framebuffer
        pixel_buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')

    offscreen.free()
    
    # Convert buffer to flat list and normalize
    pixel_buffer.dimensions = width * height * 4
    target_image.pixels = [v / 255 for v in pixel_buffer]
    
    #Save RGBD
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(target_image.name)
    target_image.filepath_raw = outDir + "/" + target_image.name + ".png"
    target_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    target_image.save()


# The CPU functions don't use bgl, so they remain largely unchanged
def saturate(num, floats=True):
    if num <= 0:
        num = 0
    elif num > (1 if floats else 255):
        num = (1 if floats else 255)
    return num

def maxEps(x):
    return max(x, 1e-6)

def encodeImageRGBMCPU(image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    for i in range(0, num_pixels, 4):
        for j in range(3):
            result_pixel[i+j] *= 1.0 / maxRange
        result_pixel[i+3] = saturate(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2], 1e-6))
        result_pixel[i+3] = math.ceil(result_pixel[i+3] * 255.0) / 255.0
        for j in range(3):
            result_pixel[i+j] /= result_pixel[i+3]
    
    target_image.pixels = result_pixel
    
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(target_image.name)
    target_image.filepath_raw = outDir + "/" + target_image.name + ".png"
    target_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    target_image.save()


def encodeImageRGBDCPU(image, maxRange, outDir, quality):
    input_image = bpy.data.images[image.name]
    image_name = input_image.name

    if input_image.colorspace_settings.name != 'Linear':
        input_image.colorspace_settings.name = 'Linear'

    if image_name[-4:] == '.exr' or image_name[-4:] == '.hdr':
        image_name = image_name[:-4]

    target_image = bpy.data.images.get(image_name + '_encoded')
    if not target_image:
        target_image = bpy.data.images.new(
                name = image_name + '_encoded',
                width = input_image.size[0],
                height = input_image.size[1],
                alpha = True,
                float_buffer = False
                )
    
    num_pixels = len(input_image.pixels)
    result_pixel = list(input_image.pixels)

    rgbdMaxRange = 255.0

    for i in range(0, num_pixels, 4):
        maxRGB = maxEps(max(result_pixel[i], result_pixel[i+1], result_pixel[i+2]))
        D = max(rgbdMaxRange/maxRGB, 1.0)
        D = np.clip((math.floor(D) / 255.0), 0.0, 1.0)

        result_pixel[i] = math.pow(result_pixel[i] * D, 1/2.2)
        result_pixel[i+1] = math.pow(result_pixel[i+1] * D, 1/2.2)
        result_pixel[i+2] = math.pow(result_pixel[i+2] * D, 1/2.2)
        result_pixel[i+3] = D
    
    target_image.pixels = result_pixel
    
    if bpy.context.scene.TLM_SceneProperties.tlm_verbose:
        print(target_image.name)
    target_image.filepath_raw = outDir + "/" + target_image.name + ".png"
    target_image.file_format = "PNG"
    bpy.context.scene.render.image_settings.quality = quality
    target_image.save()
