# Silent Hill 4 PC/Win bone mesh bin file loader with texture support
# - Alanm1
#  
# Acknowlegement:
# orignal SH4 bone mesh loader by Durik256
#  topic on forum https://reshax.com/topic/513-silent-hill-4-xbox-models-bin/#comment-1854
#
# Laurynas Zubavičius (Sparagas)  and Rodolfo Nuñez (roocker666) - Silent hill file format
# https://github.com/Sparagas/Silent-Hill
#
# HunterStanton - SH4 bin file and texture format research
# https://github.com/HunterStanton/sh4bin
# https://github.com/HunterStanton/sh4texturetool
#

from inc_noesis import *
from operator import itemgetter

def registerNoesisTypes():
    handle = noesis.register("Silent Hill 4 (PC/Win) bone mesh in bin file", ".bin")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    #noesis.logPopup()
    return 1

def noepyCheckType(data):
    filepath = os.path.basename(rapi.getInputName())
    basename  = os.path.splitext(os.path.basename(filepath))[0]    
    bs=NoeBitStream(data)
    n = bs.readUInt()
    ofs = bs.read('%iI'%n)
    tex_found = False
    mesh_found = False
    for x in ofs:        
        bs.seek(x)
        chunk_start = bs.tell()
        magic = bs.readBytes(2)
        magic2 = bs.readBytes(2)        
        if magic == magic2: #  a texture chunk
            hd = bs.read('15I')
            bs.seek(x + hd[3]) # first texture info block
            info = bs.read('4I')
            if info[3] == 0: # pc/win does not have offset value
                tex_found = True
        elif magic == b'\x03\x00' and magic2 == b'\xFF\xFF':
            mesh_found = True
        elif magic == b'\x01\x00' and magic2 == b'\x03\xFC': # do not pick up bin file that has world mesh
            if basename != 'phe_rl01':
                return 0
    if mesh_found and tex_found:
        return 1         
    return 0



def LoadTexture(data, tex_chunkList):
    bs = NoeBitStream(data)
    n_chunk = bs.readUInt()
    offs = struct.unpack("I"*n_chunk, bs.read(n_chunk*4))

    tex_id = 0            
    for i in range(n_chunk):   # looking for texture chunk
        bs.seek(offs[i])
        magic=bs.readUShort()
        magic2=bs.readUShort()
  
        if magic !=0 and magic == magic2:             
            chunk_id = i

            texList = []

            bs.seek(0xc,NOESEEK_REL)
            total_tex = magic + magic2
            n_tex_grp = magic
            bs.seek(total_tex * 0x4 + n_tex_grp*0x10,NOESEEK_REL)
            image_cnt=[]
            tex_offs=[]
            
            offs_base = bs.tell()
            for t in range(n_tex_grp): # texture header offsets
                entry_start = bs.tell()
                bs.readUInt()
                image_cnt.append(bs.readUInt())
                bs.readUInt()
                tex_offs.append((bs.readUInt() + entry_start))
            print ("image cnt",image_cnt)
            for t in range(n_tex_grp):

                bs.seek(tex_offs[t])  # jump to texture header
                for s in range(image_cnt[t]):  # Texture can have more than one image
                    tex_start = bs.tell()
                    bs.seek(0x20,NOESEEK_REL)
                    ddsWidth = bs.readUInt()
                    ddsHeight = bs.readUInt()
                    formatBytes = bs.read(4)
                    if formatBytes[2] != 0:
                        format = formatBytes.decode('utf-8')
                    else:
                        format = hex(formatBytes[0]) # not a DXT string
                    mip_cnt = bs.readUInt()
                    ddsSize = bs.readUInt()

                    bs.seek(0x1c,NOESEEK_REL)
                    imgDataOffs = struct.unpack("I"*7, bs.read(4*7))
                    unknown = bs.readUInt()
                    pos = bs.tell()
                    bs.seek(imgDataOffs[0] + tex_start)  # only load first mipmap, highest resolution
                    texName = "Tex_" + str(tex_id) + "_" + str(t) + "_"  + str(s)   # image_chunk_grpindex_subindex           

                    print(texName,ddsWidth,ddsHeight,format,mip_cnt,hex(ddsSize))                                        
                    ddsData = bs.readBytes(ddsSize)                                      

                    if format == 'DXT1':
                        dxt =  noesis.NOESISTEX_DXT1
                    elif format == 'DXT3':
                        dxt =  noesis.NOESISTEX_DXT3
                    elif format == 'DXT5':
                        dxt =  noesis.NOESISTEX_DXT5
                    else:                        
                        print ("non-compressed texture!!!")    
                        dxt = noesis.NOESISTEX_RGBA32   # if it is not DXT , last guess would be a raw uncompress image
                        dds_array = bytearray(ddsData)                        
                        for j in range(0, len(dds_array), 4): #swap red and blue channel
                            dds_array[j], dds_array[j + 2] = dds_array[j + 2], dds_array[j]
                        ddsData = bytes(dds_array)
                    texture=NoeTexture(texName, ddsWidth, ddsHeight, ddsData, dxt)
                    texNameList.append((texName,texture))
                    texList.append(texture)
                    bs.seek(pos)       
            tex_id += 1
            tex_chunkList.append(texList)    
    return 1

# specail mesh to texture mapping for wp_model.bin    
wp_model_tex_chunk=[1,2,3,4,5,6,7,8,8,9,9,10,10,11,11,12,12,13,13,14,14,15,15,16,16,17,17,18,18,19,19,20,21,22,23,24,25,26,27,28,29,30,31]
tw_mob_tex_chunk=[0,0,0,0,1,1,1,1,2,2,2,2]
tw_cars_tex_chunk=[1,1,1,1,1,1,2,1,1,2,2,1,2,2,1,3,3,3,1,1,3,3,3,3,0,3,1,3,3]
eil_arms_tex_chunk=[1,2,3,4,5]
#handle haunting texture assigment , each element specify a model's texture idx. (mesh0_all_mesh_tex_idx, mesh1_first_mesh_tex_idx, mesh1_other_mesh_tex_idx)
phe_rl01_tex_chunk=[(0,2,0),(0,3,1),(0,0,0),(4,5,5),(0,0,0),(0,0,0),(0,0,0),(0,0,0),(1,1,1),(1,1,1),(1,1,1),(1,1,1),(6,6,6),(7,7,7),(0,0,0),(1,1,1)]

def noepyLoadModel(data, mdlList):
    bs = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()   
    
    global bones, mtrlList, texNameList, basename, mtrlNameSet
    tex_chunkList = []
    texNameList = []
    mtrlNameSet = set()
    filepath = os.path.basename(rapi.getInputName())
    basename  = os.path.splitext(os.path.basename(filepath))[0]

    LoadTexture(data,tex_chunkList)
    if basename=="tw_cars":    # make shodow texture available to all vehicle models
        n_texchunk = len(tex_chunkList)
        for x in range(1,n_texchunk):
            tex_chunkList[x].extend(tex_chunkList[0])  # add shodaw texture [0] to other texture chunk
    n_tex_chunk = len(tex_chunkList)
                
    n = bs.readUInt()
    ofs = bs.read('%iI'%n)
    print('ofs:',ofs)
    model_id = 0
    for x in ofs:
        bs.seek(x)        
        magic = bs.readBytes(4)
        if magic == b'\x03\x00\xFF\xFF':
            print ("Model :",str(model_id))

            rapi.rpgSetActiveContext(ctx)              
            rapi.rpgReset()      # reset context before next model is loaded
            bones=[]
            mtrlList=[]    
            readMesh(bs,model_id) 
                  
            try:
                mdl = rapi.rpgConstructModel()
            except:
                mdl = NoeModel()

            mdl.setBones(bones)

            if basename=="phe_rl01":
                texs=[]
                t1,t2,t3=phe_rl01_tex_chunk[model_id]
                texs.append(texNameList[t1][1])
                if t1 != t2:
                    texs.append(texNameList[t2][1])
                if t2 != t3:
                    texs.append(texNameList[t3][1])
            else:
                if basename=="eil_arms":
                    use_chunk = eil_arms_tex_chunk[model_id]                                                
                elif basename=="tw_cars":
                    use_chunk = tw_cars_tex_chunk[model_id]                                                
                elif basename=="tw_mob":
                    use_chunk = tw_mob_tex_chunk[model_id]    
                elif basename=="wp_model":
                    use_chunk = wp_model_tex_chunk[model_id]
                else:
                    use_chunk = model_id                
                if use_chunk >= n_tex_chunk:
                    use_chunk = n_tex_chunk - 1
                texs =  tex_chunkList[use_chunk]
            if True:
                mdl.setModelMaterials(NoeModelMaterials(texs, mtrlList))           
            else:
                all_texs = []
                if model_id == 0:
                    for t in tex_chunkList:
                        all_texs.extend(t)      
                    mdl.setModelMaterials(NoeModelMaterials(all_texs, mtrlList))  
                
            mdlList.append(mdl)
            model_id += 1    
    return 1
    
def readMesh(bs,model_id):
    global bones
    cpos = bs.tell() - 4
    prefix = '{0:#010x}_'.format(cpos)
    hd = bs.read('16I')
    print(hd)

    bs.seek(cpos+hd[3]) 
    # bone parent index
    pi = bs.read('%ib'%hd[2])
    
    boneMat=[]
    bs.seek(cpos+hd[1])
    # bone matrices
    for x in range(hd[2]):
        mat = NoeMat44.fromBytes(bs.readBytes(64))
        # save original matrix for mesh transform 
        boneMat.append(copy.deepcopy(mat))
        mat=mat.toMat43()
        trans = mat [3]                     
        # flip horizontal and virtical position
        mat[3] = (-trans[0],-trans[1], trans[2])

        # set up skeleton with flipped matrix
        bones.append(NoeBone(x,'bone_%i'%x,mat,None,pi[x]))       
    # get bonePair array
    bs.seek(cpos+hd[5])
    _bp=[]
    for i in range(hd[4]):
        _bp.append([bs.readByte(),bs.readByte()]) #[parent_id, child_id]
    print ( "bp ",_bp)

    mtrlMap={}

    bs.seek(cpos+hd[14]) # material/texture array
    for x in range(hd[13]): # num material
        mrtl_group=bs.readUInt()
        mtrlMap[x]=bs.readBytes(4)
    print("material ",mtrlMap)

    #print ("model ",str(model_id), "no of mesh0 ", str(hd[7]))
    bs.seek(cpos+hd[8])
    for x in range(hd[7]):
        readSM(bs,"Mesh"+str(model_id),0,model_id, x,bones,_bp,boneMat,mtrlMap)
    #print ("model ",str(model_id), "no of mesh1 ", str(hd[9]))
    bs.seek(cpos+hd[10])
    for x in range(hd[9]):
        readSM(bs,"Mesh"+str(model_id),1,model_id, x,bones,_bp,boneMat,mtrlMap)
    return 1



def readSM(bs,prefix,mesh_grp,model_id, x,bones,bone_pair,boneMat,mtrlMap):
    m_start = bs.tell()
    inf = bs.read('16I')
    
    bs.seek(m_start+inf[8])  # bone list 
    bi0 = bs.read('%iH'%inf[7]) 
    bs.seek(m_start+inf[10])  # bone pair list
    bi1 = bs.read('%iH'%inf[9])
    bonemap = []
    bonemap.extend(bi0)
    # bi1 are indices for bone_pair table, append  child bone of pair to bonemap
    bonemap.extend([bone_pair[bpi][1] for bpi in bi1])
    #print ("bonemap ",len(bonemap),bonemap)

    material_id = bs.readUShort()    
    tex_id = mtrlMap[material_id]  # material with texture
    tex_grp = tex_id[0] - 1
    tex_sub = tex_id[1]

    
    mtrlName = "Mat_" + str(model_id) + "_" + str(material_id)

    if mtrlName not in mtrlNameSet:
        mtrlNameSet.add(mtrlName)
        if basename == "phe_rl01":
            t1,t2,t3=phe_rl01_tex_chunk[model_id]
            if mesh_grp == 0:
                texName=texNameList[t1][0]
            else:
                if x == 0:
                    texName=texNameList[t2][0]
                else:
                    texName=texNameList[t3][0]                
        else:
            if basename == "tw_cars":
                if mesh_grp  > 0:
                    tex_id = 0  # point to shadow texture grp
                    if model_id == 4:
                        tex_grp = 0
                else:
                    tex_id = tw_cars_tex_chunk[model_id]
            elif basename == "eil_arms":
                tex_id = eil_arms_tex_chunk[model_id]
            elif basename == "tw_mob":
                tex_id = tw_mob_tex_chunk[model_id]        
            elif basename == "wp_model":  #special texture rule
                tex_id = wp_model_tex_chunk[model_id]        
            else:
                tex_id = model_id
            texName = "Tex_" + str(tex_id) + "_" + str(tex_grp) + "_" + str(tex_sub)        
        mtrlList.append( NoeMaterial(mtrlName,texName))
        print ("material id", material_id, mtrlName, texName)
    rapi.rpgSetMaterial(mtrlName)  # assign material
    
    bs.seek(m_start+inf[2])  # skip header size
    
    v_hd_start = bs.tell()
    n_submesh = bs.readUInt()
    bs.readUInt()
    ibuf_ofs = bs.readUInt()
    
    submesh=[]
    for s in range(n_submesh):
        bs.seek(0x40,1)
        #i_cnt , v_cnt, v_size ,face_id ,i_ofs , _ ,_ 
        i_hd = bs.read("7I")
        submesh.append(i_hd)

    # transform vertices pos/normal with bones matrix of first bone 
    for s in range(n_submesh):        
        v_size = submesh[0][2]
        biid_map = {}
        vbuf = bs.readBytes(submesh[s][1]* submesh[s][2]) # v_cnt * v_size

        last_v = bs.tell()

        bid_set = set()  # collect all bonemap index id        
        bs.seek(v_hd_start  + ibuf_ofs + s* 0x5c + submesh[s][4])
        ibuf = bs.read("H"*submesh[s][0])        
        bs.seek(v_hd_start  + ibuf_ofs + s* 0x5c + submesh[s][6])
        biid_tab = bs.read("I"*20) # bonemap idx table, map bone map index_id to bonemap idx

        bs.seek(last_v)
        
        if submesh[s][2] >32:
            for idx in ibuf:
                v_idx = idx * v_size
                bi_tmp = [ x for x in struct.unpack("4f",vbuf[v_idx+32:v_idx+48])]
                bw_tmp = [ x for x in struct.unpack("4f",vbuf[v_idx+48:v_idx+64])]
                for i,w in enumerate(bw_tmp):
                    bid_set.add(bi_tmp[i])                
            biid_list = sorted(bid_set)

            for i,biid in enumerate(biid_list):      # map bone map index id to bone map index
                    if biid not in biid_map:   
                        biid_map[biid] = biid_tab[i]
        v_set = set()
        v_size =submesh[s][2]
        fvbuf = bytearray(vbuf)  # mutable byte array
        for idx in ibuf:     #  convert vertex buffer bone map index id to bone map index
            if idx not in v_set:
                v_set.add(idx)
                v_idx = idx * v_size 
                vx,vy,vz = struct.unpack("fff",vbuf[v_idx:v_idx+12])
                nx,ny,nz = struct.unpack("fff",vbuf[v_idx+12:v_idx+24])
                if submesh[s][2] >32:                    
                    bw = [ x for x in struct.unpack("4f",vbuf[v_idx+48:v_idx+64])]
                    bi = [biid_map[x] for x in struct.unpack("4f",vbuf[v_idx+32:v_idx+48])]
                    # mesh need to be transform to first bone position
                    bone = bonemap[bi[0]]
                    mat = boneMat[bone]
                else:
                    mat = boneMat[0]
                vert = NoeVec4((vx,vy,vz,1))
                norm = NoeVec4((nx,ny,nz,0))
                # transform vertices and normals to vertex first bone position
                newv = mat * vert
                newn = mat * norm
                # pack transformed position, normal, bonemap index back to vbuf
                fvbuf[v_idx:v_idx+12]=noePack('3f', newv[0],newv[1],newv[2])
                fvbuf[v_idx+12:v_idx+24]=noePack('3f', newn[0],newn[1],newn[2])
                if v_size > 32:
                    fvbuf[v_idx+32:v_idx+48]=noePack('4I', *bi)
                    fvbuf[v_idx+48:v_idx+64]=noePack('4f', *bw)                                
            
        
        v_buf =  bytes(fvbuf)  #  back to bytes

        # flip mesh along x and y-axis to match flipped skeleton
        rapi.rpgSetTransform(NoeMat43((NoeVec3((-1, 0, 0)), NoeVec3((0, -1, 0)), NoeVec3((0, 0, 1)), NoeVec3((0, 0, 0)))))   
        
        rapi.rpgSetBoneMap(bonemap)        

        i_buf = noePack('H'*submesh[s][0],*ibuf)  # convert to bytes

        rapi.rpgBindPositionBufferOfs(v_buf, noesis.RPGEODATA_FLOAT, 64, 0)

        rapi.rpgBindNormalBufferOfs(v_buf, noesis.RPGEODATA_FLOAT, 64, 12)        

        rapi.rpgBindUV1BufferOfs(v_buf, noesis.RPGEODATA_FLOAT, 64, 24)
        if v_size >32:
            rapi.rpgBindBoneIndexBufferOfs(v_buf,noesis.RPGEODATA_UINT,64,32,4)
            rapi.rpgBindBoneWeightBufferOfs(v_buf,noesis.RPGEODATA_FLOAT,64,48,4)            

        mesh_name = prefix + "_"+str(mesh_grp)+"_"+str(x) + "_" + str(s)   
        print(mesh_name)     
        rapi.rpgSetName(mesh_name)
        rapi.rpgCommitTriangles(i_buf, noesis.RPGEODATA_USHORT, submesh[s][0], noesis.RPGEO_TRIANGLE_STRIP)
        rapi.rpgClearBufferBinds() #reset in case a subsequent mesh doesn't have the same components
    bs.seek(m_start+inf[0])

    