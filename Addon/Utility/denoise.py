import bpy, platform, subprocess, os
import numpy as np
from . import utility

def check_denoiser_path(self, scene):

    #TODO - Apply for Optix too...

    if scene.TLM_SceneProperties.tlm_denoise_use:
        if scene.TLM_SceneProperties.tlm_oidn_path == "":
            print("NO DENOISE PATH")
            return False
        else:
            #MAKE DETAILED CHECK FOR DENOISE FILE
            return True
    else:
        return True

def denoise_lightmaps(scene):

    #ATLAS DENOISING?

    filepath = bpy.data.filepath
    dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_SceneProperties.tlm_lightmap_savedir)

    for atlasgroup in scene.TLM_AtlasList:
        atlas_name = atlasgroup.name
        atlas_items = []

        img_name = atlas_name + '_baked'
        bakemap_path = os.path.join(dirpath, img_name)

        if scene.TLM_SceneProperties.tlm_denoise_use:
            if scene.TLM_SceneProperties.tlm_denoiser == "Optix":

                image_output_destination = bakemap_path + ".hdr"
                denoise_output_destination = bakemap_path + "_denoised.hdr"

                if platform.system() == 'Windows':
                    optixPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_optix_path),"Denoiser.exe")
                    pipePath = [optixPath, '-i', image_output_destination, '-o', denoise_output_destination]
                elif platform.system() == 'Darwin':
                    print("Mac for Optix is still unsupported")    
                else:
                    print("Linux for Optix is still unsupported")

                if scene.TLM_SceneProperties.tlm_optix_verbose:
                    denoisePipe = subprocess.Popen(pipePath, shell=True)
                else:
                    denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)

                denoisePipe.communicate()[0]
                
                image = bpy.data.images[img_name]
                bpy.data.images[image.name].filepath_raw = bpy.data.images[image.name].filepath_raw[:-4] + "_denoised.hdr"
                bpy.data.images[image.name].reload()

            else: #OIDN

                image = bpy.data.images[img_name]
                width = image.size[0]
                height = image.size[1]

                image_output_array = np.zeros([width, height, 3], dtype="float32")
                image_output_array = np.array(image.pixels)
                image_output_array = image_output_array.reshape(height, width, 4)
                image_output_array = np.float32(image_output_array[:,:,:3])

                image_output_destination = bakemap_path + ".pfm"

                with open(image_output_destination, "wb") as fileWritePFM:
                    utility.save_pfm(fileWritePFM, image_output_array)

                denoise_output_destination = bakemap_path + "_denoised.pfm"

                Scene = scene

                verbose = Scene.TLM_SceneProperties.tlm_oidn_verbose
                affinity = Scene.TLM_SceneProperties.tlm_oidn_affinity

                if verbose:
                    print("Denoiser search: " + os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe"))
                    v = "3"
                else:
                    v = "0"

                if affinity:
                    a = "1"
                else:
                    a = "0"

                threads = str(Scene.TLM_SceneProperties.tlm_oidn_threads)
                maxmem = str(Scene.TLM_SceneProperties.tlm_oidn_maxmem)

                if platform.system() == 'Windows':
                    oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe")
                    pipePath = [oidnPath, '-f', 'RTLightmap', '-hdr', image_output_destination, '-o', denoise_output_destination, '-verbose', v, '-threads', threads, '-affinity', a, '-maxmem', maxmem]
                elif platform.system() == 'Darwin':
                    oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                    pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                else:
                    oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                    pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                    
                if not verbose:
                    denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                else:
                    denoisePipe = subprocess.Popen(pipePath, shell=True)

                denoisePipe.communicate()[0]

                with open(denoise_output_destination, "rb") as f:
                    denoise_data, scale = utility.load_pfm(f)

                ndata = np.array(denoise_data)
                ndata2 = np.dstack((ndata, np.ones((width,height))))
                img_array = ndata2.ravel()
                bpy.data.images[image.name].pixels = img_array
                bpy.data.images[image.name].filepath_raw = bakemap_path + ".hdr"
                bpy.data.images[image.name].file_format = "HDR"
                bpy.data.images[image.name].save()

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if obj.TLM_ObjectProperties.tlm_mesh_lightmap_use:

                if not obj.TLM_ObjectProperties.tlm_mesh_lightmap_unwrap_mode == "AtlasGroup":
                    #IF NOT ATLAS GROUP

                    img_name = obj.name + '_baked'
                    bakemap_path = os.path.join(dirpath, img_name)

                    #Denoise here
                    if scene.TLM_SceneProperties.tlm_denoise_use:
                        
                        #Optix
                        if scene.TLM_SceneProperties.tlm_denoiser == "Optix":

                            image_output_destination = bakemap_path + ".hdr"
                            denoise_output_destination = bakemap_path + "_denoised.hdr"

                            if platform.system() == 'Windows':
                                optixPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_optix_path),"Denoiser.exe")
                                pipePath = [optixPath, '-i', image_output_destination, '-o', denoise_output_destination]
                            elif platform.system() == 'Darwin':
                                print("Mac for Optix is still unsupported")    
                            else:
                                print("Linux for Optix is still unsupported")

                            if scene.TLM_SceneProperties.tlm_optix_verbose:
                                denoisePipe = subprocess.Popen(pipePath, shell=True)
                            else:
                                denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)

                            denoisePipe.communicate()[0]
                            
                            image = bpy.data.images[img_name]
                            bpy.data.images[image.name].filepath_raw = bpy.data.images[image.name].filepath_raw[:-4] + "_denoised.hdr"
                            bpy.data.images[image.name].reload()

                        else: #OIDN

                            image = bpy.data.images[img_name]
                            width = image.size[0]
                            height = image.size[1]

                            image_output_array = np.zeros([width, height, 3], dtype="float32")
                            image_output_array = np.array(image.pixels)
                            image_output_array = image_output_array.reshape(height, width, 4)
                            image_output_array = np.float32(image_output_array[:,:,:3])

                            image_output_destination = bakemap_path + ".pfm"

                            with open(image_output_destination, "wb") as fileWritePFM:
                                utility.save_pfm(fileWritePFM, image_output_array)

                            denoise_output_destination = bakemap_path + "_denoised.pfm"

                            Scene = scene

                            verbose = Scene.TLM_SceneProperties.tlm_oidn_verbose
                            affinity = Scene.TLM_SceneProperties.tlm_oidn_affinity

                            if verbose:
                                print("Denoiser search: " + os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe"))
                                v = "3"
                            else:
                                v = "0"

                            if affinity:
                                a = "1"
                            else:
                                a = "0"

                            threads = str(Scene.TLM_SceneProperties.tlm_oidn_threads)
                            maxmem = str(Scene.TLM_SceneProperties.tlm_oidn_maxmem)

                            if platform.system() == 'Windows':
                                oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise.exe")
                                pipePath = [oidnPath, '-f', 'RTLightmap', '-hdr', image_output_destination, '-o', denoise_output_destination, '-verbose', v, '-threads', threads, '-affinity', a, '-maxmem', maxmem]
                            elif platform.system() == 'Darwin':
                                oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                                pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                            else:
                                oidnPath = os.path.join(bpy.path.abspath(scene.TLM_SceneProperties.tlm_oidn_path),"denoise")
                                pipePath = [oidnPath + ' -f ' + ' RTLightmap ' + ' -hdr ' + image_output_destination + ' -o ' + denoise_output_destination + ' -verbose ' + v]
                                
                            if not verbose:
                                denoisePipe = subprocess.Popen(pipePath, stdout=subprocess.PIPE, stderr=None, shell=True)
                            else:
                                denoisePipe = subprocess.Popen(pipePath, shell=True)

                            denoisePipe.communicate()[0]

                            with open(denoise_output_destination, "rb") as f:
                                denoise_data, scale = utility.load_pfm(f)

                            ndata = np.array(denoise_data)
                            ndata2 = np.dstack((ndata, np.ones((width,height))))
                            img_array = ndata2.ravel()
                            bpy.data.images[image.name].pixels = img_array
                            bpy.data.images[image.name].filepath_raw = bakemap_path + ".hdr"
                            bpy.data.images[image.name].file_format = "HDR"
                            bpy.data.images[image.name].save()

                else:

                    pass