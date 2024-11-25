from alinea.caribu.CaribuScene import CaribuScene
from alinea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun
from openalea.plantgl.all import *
from pgljupyter import SceneWidget
from numpy import arange, random
import matplotlib.pyplot as plt
from openalea.lpy import Lsystem
from ipywidgets import interact, interactive, fixed, interact_manual, widgets
from math import ceil, floor
from IPython.display import display
import pandas as pd

import sys, os
from os.path import join, exists
canpaths = [join(sys.prefix,'bin'),join(sys.prefix,'Scripts'),join(sys.prefix,'Library','mingw-w64','bin'),join(sys.prefix,'Library','bin')]
for canpath in canpaths:
    if exists(canpath) and canpath not in os.environ['PATH']: 
        os.environ['PATH']+=os.pathsep+canpath


def reformat_scene(geometry):
    nbpolygons = len(geometry.indexList)
    sc = Scene()
    for i in range(nbpolygons):
        pts = [geometry.pointAt(i, j) for j in range(3)]
        c = geometry.colorList[i]
        sc.add(Shape(TriangleSet(pts, [list(range(3))]), Material((c.red, c.green, c.blue), 1, transparency=c.clampedAlpha())))
    return sc


def Light_model(lsys, hour=12):
    lstring = lsys.get_lstring()
    scene = lsys.scene['scene']
    # Creates sun
    energy = 1
    DOY = 175
    latitude = 46.4333
    getsun = GetLightsSun.GetLightsSun(Gensun.Gensun()(energy, DOY, hour, latitude)).split(' ')
    sun = tuple((float(getsun[0]), tuple((float(getsun[1]), float(getsun[2]), float(getsun[3])))))
    sun_position = sun
    # print (sun_position)
    sunid = 1000000
    sun_shp = Shape(Translated(sun_position[1][0] * -50, sun_position[1][1] * -50, sun_position[1][2] * -50, Sphere(0.5)), Material(Color3(60, 60, 15)), id=sunid)
    if scene[-1].id != sunid:
        scene.add(sun_shp)
    else:
        scene[-1] = sun_shp

    c_scene = CaribuScene(scene=scene, light=[sun])
    # SceneWidget(scene)
    raw, aggregated = c_scene.run()

    # Visualisation
    viewmaponcan, _ = c_scene.plot(raw['default_band']['Eabs'], display=False)

    #  Fred's hack to display the scene with colors using pgl-jupyter widgets
    colored_scene = Scene()
    for shp in viewmaponcan:
        colored_scene.add(reformat_scene(shp.geometry))

    #  Graph
    graph = {'Tige': 0, 'Feuilles': 0}
    for vid, Eabs in aggregated['default_band']['Eabs'].items():
        if vid == 0 or vid >= len(lstring):
            continue
        elif lstring[vid].name in 'FT':
            graph['Feuilles'] += Eabs / sum(aggregated['default_band']['Eabs'].values())
        else:
            graph['Tige'] += Eabs / sum(aggregated['default_band']['Eabs'].values())

    fig, ax = plt.subplots()

    LIE = sum(aggregated['default_band']['Eabs'][k]*aggregated['default_band']['area'][k]*1E-4 for k in aggregated['default_band']['Eabs']) / (sum(aggregated['default_band']['area'].values())*1E-4)
    print("Efficience interception lumière = {}".format(LIE))

    print(graph)
    xindex = [1, 2]
    LABELS = graph.keys()
    ax.bar(xindex, graph.values(), align='center')
    plt.xticks(xindex, LABELS)
    ax.set_yticks(arange(0, 1.2, 0.2))
    ax.set_ylabel('Proportion interception PAR')
    return SceneWidget(colored_scene, size_world=75)


def Run_AgriPV(agripv = True, interpanel=400, nb_plantes_caribu = 5, panelsize = 50, angle_panel = 0, height_panel = 100, flag_couvert = 'Luzerne',  sky = True, sun = True, hour = 12,infini = True):    
    def Calcul_Caribu(scene, pattern_caribu, infini, dico_IDs, sky=sky, sun=sun, hour=hour,height_panel=height_panel):
        # ciel
        lights = []
        if sky:
            sky_string = GetLight.GetLight(GenSky.GenSky()(450, 'uoc', 4, 5))  # (Energy, soc/uoc, azimuts, zenits)
            #sky_string = GetLight.GetLight(GenSky.GenSky()(450, 'uoc', 36, 9))  # (Energy, soc/uoc, azimuts, zenits)
        


            for string in sky_string.split('\n'):
                if len(string) != 0:
                    string_split = string.split(' ')
                    t = tuple((float(string_split[0]), tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))))
                    lights.append(t)
        
        if sun :
            # Creates sun
            energy = 1050
            DOY = 175
            latitude = 46.4333
            getsun = GetLightsSun.GetLightsSun(Gensun.Gensun()(energy, DOY, hour, latitude)).split(' ')
            sun = tuple((float(getsun[0]), tuple((float(getsun[1]), float(getsun[2]), float(getsun[3])))))
            lights.append(sun)
            # print (sun_position)

        c_scene = CaribuScene(scene=scene, light=lights, pattern=pattern_caribu)
        raw, aggregated = c_scene.run(direct=True, infinite=infini)

        # Visualisation
        viewmaponcan, _ = c_scene.plot(raw['default_band']['Eabs'], display=False)

        #  Fred's hack to display the scene with colors using pgl-jupyter widgets
        colored_scene = Scene()
        for shp in viewmaponcan:
            colored_scene.add(reformat_scene(shp.geometry))
            if sun:
                sunid = 1000000
                sun_shp = Shape(Translated(sun[1][0] * -height_panel*1.5, sun[1][1] * -height_panel*1.5, sun[1][2] * -height_panel*1.5, Sphere(5)), Material(Color3(60, 60, 15)), id=sunid)
                if colored_scene[-1].id != sunid:
                    colored_scene.add(sun_shp)
                else:
                    colored_scene[-1] = sun_shp


        # Graph
        graph = {}
        eabs_total = sum(eabs * area for (eabs, area) in zip(aggregated['default_band']['Eabs'].values(), aggregated['default_band']['area'].values()))
        
        for vid, Eabs in aggregated['default_band']['Eabs'].items():
            #if vid >= 1000:
            #    graph['luzerne'] += Eabs * aggregated['default_band']['area'][vid] / eabs_total
            #else:
            #    graph['fetuque'] += Eabs * aggregated['default_band']['area'][vid] / eabs_total
            if vid in [*dico_IDs[[*dico_IDs][0]].keys()]:
                graph[dico_IDs[[*dico_IDs][0]][vid]] = Eabs

        #print([*graph.values()])
        df = pd.DataFrame({'Plant Id' : graph.keys(), 'Rayonnement intercepte' : [round(i,2) for i in graph.values()]})
        df.set_index('Plant Id', drop=True,inplace=True)
        display(df)

        fig, ax = plt.subplots()
        xindex = [*graph.keys()]
        LABELS = graph.keys()
        ax.bar(xindex, graph.values(), align='center')
        plt.xticks(xindex, LABELS)
        # ax.set_yticks(arange(0, 1., 0.1))
        ax.set_ylabel("Radiation interception")

        return colored_scene

    # Makes Lsystem for association
    scaling_Lmax = 1
    inclination_factor = 1
    #print(len(s_vig))

    # Visualisation of the association
    scene_out, scene_out_caribu = Scene(), Scene()


    #distance_plante = 10.
    initID = 1000
    distance = interpanel#*100 #conversion en cm
    #nb_plantes = round(2.*distance/distance_plante)+1
    distance_plante = distance/nb_plantes_caribu
    nb_plt_g = floor((nb_plantes_caribu-1)/2)
    nb_plt_d = ceil((nb_plantes_caribu-1)/2)
    #informations panneaux
    #panelsize = 10
    #angle_panel = 0
    #height_panel = 0
    
    #panel = QuadSet([(panelsize/2, -panelsize/2,0),
    #                 (panelsize/2+panelsize, -panelsize/2,0),
    #                 (panelsize/2+panelsize, panelsize/2,0),
    #                 (panelsize/2, panelsize/2,0)],[list(range(4))])
    panel = QuadSet([(-distance_plante/2, -panelsize/2,0),
                     (distance_plante/2, -panelsize/2,0),
                     (distance_plante/2, panelsize/2,0),
                     (-distance_plante/2, panelsize/2,0)],[list(range(4))])

    sensor = QuadSet([(-2.5, -2.5,0),
                     (2.5, -2.5,0),
                     (2.5, 2.5,0),
                     (-2.5, 2.5,0)],[list(range(4))])

    ######Dictionnaire des Ids des plantes qui sont entre les panneaux
    dico_Ids = {}
    dico_pltes_Ids = {}
    no_plte_res = nb_plt_g+1
    
    #print('distance avant', distance, distance_plante, nb_plantes_caribu, nb_plt_g, nb_plt_d)
    ########plante sous le panneau########################
    #print('sous pv')

    if (flag_couvert=='Luzerne'):
        lsys_luz = Lsystem('TD_lsystem_Luzerne.lpy', {'scaling_Lmax': scaling_Lmax, 'inclination_factor': inclination_factor})
        lsys_luz_str = lsys_luz.derive()
        s_luz = lsys_luz.sceneInterpretation(lsys_luz_str)
        dico_Ids[no_plte_res*initID] = no_plte_res
        azimut_plante = random.random()*3.14
        for shp in s_luz:
            scene_out_caribu += Shape(Translated(0, 0, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
            
    elif (flag_couvert=='Fétuque'):
        lsys_fet = Lsystem('TD_lsystem_Fetuque.lpy')
        lsys_fet_str = lsys_fet.derive()
        s_fet = lsys_fet.sceneInterpretation(lsys_fet_str)
        dico_Ids[no_plte_res*initID] = no_plte_res
        azimut_plante = random.random()*3.14
        for shp in s_fet:
            scene_out_caribu += Shape(Translated(0, 0, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)

    elif (flag_couvert=='Vigne'):
        lsys_vig = Lsystem('vigne.lpy')
        lsys_vig_str = lsys_vig.derive()
        s_vig = lsys_vig.sceneInterpretation(lsys_vig_str)
        dico_Ids[no_plte_res*initID] = no_plte_res
        for shp in s_vig:
            scene_out_caribu += Shape(Translated(0, 0, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)

    
    else:
        dico_Ids[no_plte_res*initID] = no_plte_res
        scene_out_caribu += Shape(Translated(0, 0, 0, sensor), id=no_plte_res*initID)
    #print(no_plte_res)
    #print(dico_Ids)
    #no_plte_res += 1

    
    ########plangtes d'un cote des panneaux########################
    
    #print('gauche pv')
    for num_plante in range(1,nb_plt_g+1):
        no_plte_res -= 1
        if (flag_couvert=='Luzerne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
                
        elif (flag_couvert=='Fétuque'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)

        elif (flag_couvert=='Vigne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            for shp in s_vig:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)
    
        
        else:
            dico_Ids[no_plte_res*initID]=no_plte_res
            scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, sensor), id=no_plte_res*initID)
        
        #print(no_plte_res)
        #print(dico_Ids)
    #scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 5, sensor))    

    ########plantes de l'autre cote des panneaux########################
    
    #print('droite pv')
    no_plte_res = nb_plt_g+1
    for num_plante in range(1,nb_plt_d+1):
        no_plte_res += 1
        if (flag_couvert=='Luzerne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
                
        elif (flag_couvert=='Fétuque'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
    
        elif (flag_couvert=='Vigne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            for shp in s_vig:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)
    
        
        else:
            dico_Ids[no_plte_res*initID]=no_plte_res
            scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, sensor), id=no_plte_res*initID)
        
        #print(no_plte_res)
        #print(dico_Ids)
    
    dico_pltes_Ids[flag_couvert] = dico_Ids
        
        
    ###########RAJOUT des panneaux################
    #print(len(scene_out))
    if (agripv == True):
        scene_out_caribu += Shape(Translated(0, 0, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))

    pattern_caribu = (-distance_plante/2,-(nb_plt_g+0.5)*distance_plante,distance_plante/2,(nb_plt_d+0.5)*distance_plante)
    if sun or sky:
        colored_scene = Calcul_Caribu(scene_out_caribu, pattern_caribu, infini, dico_pltes_Ids)
    else:
        colored_scene = scene_out_caribu
    xmin, ymin, xmax, ymax = pattern_caribu
    h = -1
    scene_limit = QuadSet([(xmin,ymin,h),(xmin,ymax,h),(xmax,ymax,h),(xmax,ymin,h)],[range(4)])
    colored_scene.add(Shape(scene_limit, Material(Color3(0,0,0)), id=100000000))
    #print(len(dico_pltes_Ids[flag_couvert]),pattern_caribu)
    sc = SceneWidget(colored_scene, size_world=max(100,height_panel*1.5))
    sc.plane = False
    return sc

def cellule_analyse_AgriPV():
    interact(Run_AgriPV,
             agripv = widgets.Checkbox(
                 value=True,
                 description='AgriPV',
                 disabled=False,
                 indent=False
    ),             
             interpanel=widgets.FloatSlider(
                 value=400.,
                 min=100,
                 max=1000,
                 step=10,
                 description='InterPanel',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
             ),             
             nb_plantes_caribu=widgets.IntSlider(
                 value=5,
                 min=1,
                 max=10,
                 step=1,
                 description='Nb Plantes',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='d',
             ),
             distance_plante=widgets.FloatSlider(
                 value=50.,
                 min=5.,
                 max=60.0,
                 step=5.,
                 description='InterPlantes (cm):',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
             ),
             panelsize=(10,100,10), angle_panel=(-90,90,10), height_panel=(0,400,10),
             flag_couvert = widgets.Dropdown(
                options=['Luzerne', 'Fétuque','Vigne', 'Sol'],
                value='Sol',
                description='Couvert :',
                disabled=False,
             ),
             sun = widgets.Checkbox(
                value=False,
                description="Lumière directe",
                disabled=False,
                indent=False
             ),
             sky = widgets.Checkbox(
                value=False,
                description="Lumière diffuse",
                disabled=False,
                indent=False
             ),
             hour=widgets.IntSlider(
                 value=12,
                 min=7,
                 max=18,
                 step=1,
                 description='Hour',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='d',
             ),
             infini = widgets.Checkbox(
                value=True,
                description='Couvert Infini',
                disabled=False,
                indent=False
    ));
    return



    #############PARTIE POUR UNE DIRECTION DU SOLEIL############################

def Run_AgriPV_direct(agripv = True, interpanel=3, nb_plantes_caribu = 10, panelsize = 10, angle_panel = 40, height_panel = 0, flag_couvert = 'Luzerne', infini = True, hour = 12):
    def Calcul_Caribu_direct(scene, pattern_caribu, infini, dico_IDs):
        # Creates sun
        energy = 1
        DOY = 175
        latitude = 46.4333
        getsun = GetLightsSun.GetLightsSun(Gensun.Gensun()(energy, DOY, hour, latitude)).split(' ')
        sun = tuple((float(getsun[0]), tuple((float(getsun[1]), float(getsun[2]), float(getsun[3])))))
        sun_position = sun
        # print (sun_position)
        sunid = 1000000
        sun_shp = Shape(Translated(sun_position[1][0] * -50, sun_position[1][1] * -50, sun_position[1][2] * -50, Sphere(0.5)), Material(Color3(60, 60, 15)), id=sunid)
        if scene[-1].id != sunid:
            scene.add(sun_shp)
        else:
            scene[-1] = sun_shp

        c_scene = CaribuScene(scene=scene, light=[sun], pattern=pattern_caribu)
        raw, aggregated = c_scene.run(direct=True, infinite=infini)

        # Visualisation
        viewmaponcan, _ = c_scene.plot(raw['default_band']['Eabs'], display=False)

        #  Fred's hack to display the scene with colors using pgl-jupyter widgets
        colored_scene = Scene()
        for shp in viewmaponcan:
            colored_scene.add(reformat_scene(shp.geometry))

        # Graph
        graph = {}
        eabs_total = sum(eabs * area for (eabs, area) in zip(aggregated['default_band']['Eabs'].values(), aggregated['default_band']['area'].values()))
        
        for vid, Eabs in aggregated['default_band']['Eabs'].items():
            #if vid >= 1000:
            #    graph['luzerne'] += Eabs * aggregated['default_band']['area'][vid] / eabs_total
            #else:
            #    graph['fetuque'] += Eabs * aggregated['default_band']['area'][vid] / eabs_total
            
            if vid in [*dico_IDs[[*dico_IDs][0]].keys()]:
                graph[dico_IDs[[*dico_IDs][0]][vid]] = Eabs
        print([*dico_IDs[[*dico_IDs][0]].keys()])
        print([*graph.values()])

        fig, ax = plt.subplots()
        xindex = [*graph.keys()]
        LABELS = graph.keys()
        ax.bar(xindex, graph.values(), align='center')
        plt.xticks(xindex, LABELS)
        ax.set_yticks(arange(0, 1., 0.1))
        ax.set_ylabel("Radiation interception")

        return colored_scene

    # Makes Lsystem for association
    scaling_Lmax = 1
    inclination_factor = 1
    lsys_luz = Lsystem('TD_lsystem_Luzerne.lpy', {'scaling_Lmax': scaling_Lmax, 'inclination_factor': inclination_factor})
    lsys_fet = Lsystem('TD_lsystem_Fetuque.lpy')
    lsys_vig = Lsystem('vigne.lpy')
    lsys_luz_str = lsys_luz.derive()
    lsys_fet_str = lsys_fet.derive()
    lsys_vig_str = lsys_vig.derive()
    s_luz = lsys_luz.sceneInterpretation(lsys_luz_str)
    s_fet = lsys_fet.sceneInterpretation(lsys_fet_str)
    s_vig = lsys_vig.sceneInterpretation(lsys_vig_str)
    print(len(s_vig))

    scene_asso = s_luz + s_fet
    # Visualisation of the association
    scene_out, scene_out_caribu = Scene(), Scene()

    #for shp in scene_asso:
    #    if shp.id <= 1000:  # Fetuque
    #        scene_out += Shape(Translated(distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
    #    else:  # Luzerne
    #        scene_out += Shape(Translated(-distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)

    #distance_plante = 10.
    initID = 1000
    distance = interpanel*100 #conversion en cm
    #nb_plantes = round(2.*distance/distance_plante)+1
    nb_plantes_caribu = 10
    distance_plante = distance/nb_plantes_caribu
    nb_plt_g = floor((nb_plantes_caribu-1)/2)
    nb_plt_d = ceil((nb_plantes_caribu-1)/2)
    #informations panneaux
    #panelsize = 10
    #angle_panel = 0
    #height_panel = 0
    
    #panel = QuadSet([(panelsize/2, -panelsize/2,0),
    #                 (panelsize/2+panelsize, -panelsize/2,0),
    #                 (panelsize/2+panelsize, panelsize/2,0),
    #                 (panelsize/2, panelsize/2,0)],[list(range(4))])
    panel = QuadSet([(-distance_plante/2, -panelsize/2,0),
                     (distance_plante/2, -panelsize/2,0),
                     (distance_plante/2, panelsize/2,0),
                     (-distance_plante/2, panelsize/2,0)],[list(range(4))])

    sensor = QuadSet([(-2.5, -2.5,0),
                     (2.5, -2.5,0),
                     (2.5, 2.5,0),
                     (-2.5, 2.5,0)],[list(range(4))])

    ######Dictionnaire des Ids des plantes qui sont entre les panneaux
    dico_Ids = {}
    dico_pltes_Ids = {}
    no_plte_res = 1
    
    print('distance avant', distance, distance_plante, nb_plantes_caribu, nb_plt_g, nb_plt_d)
    ########plante sous le panneau########################
    print('sous pv')
    if (flag_couvert=='Luzerne'):
        dico_Ids[no_plte_res*initID] = no_plte_res
        azimut_plante = random.random()*3.14
        for shp in s_luz:
            scene_out_caribu += Shape(Translated(0, 0, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
            
    elif (flag_couvert=='Fétuque'):
        dico_Ids[no_plte_res*initID] = no_plte_res
        azimut_plante = random.random()*3.14
        for shp in s_fet:
            scene_out_caribu += Shape(Translated(0, 0, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)

    elif (flag_couvert=='Vigne'):
        dico_Ids[no_plte_res*initID] = no_plte_res
        for shp in s_vig:
            scene_out_caribu += Shape(Translated(0, 0, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)

    
    else:
        dico_Ids[no_plte_res*initID] = no_plte_res
        scene_out_caribu += Shape(Translated(0, 0, 0, sensor), id=no_plte_res*initID)
    print(no_plte_res)
    print(dico_Ids)
    #no_plte_res += 1

    
    ########plangtes d'un cote des panneaux########################
    
    print('gauche pv')
    for num_plante in range(1,nb_plt_g+1):
        no_plte_res += 1
        if (flag_couvert=='Luzerne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
                
        elif (flag_couvert=='Fétuque'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)

        elif (flag_couvert=='Vigne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            for shp in s_vig:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)
    
        
        else:
            dico_Ids[no_plte_res*initID]=no_plte_res
            scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, sensor), id=no_plte_res*initID)
        
        print(no_plte_res)
        print(dico_Ids)
    #scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 5, sensor))    

    ########plantes de l'autre cote des panneaux########################
    
    print('droite pv')
    for num_plante in range(1,nb_plt_d+1):
        no_plte_res += 1
        if (flag_couvert=='Luzerne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
                
        elif (flag_couvert=='Fétuque'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=no_plte_res*initID)
    
        elif (flag_couvert=='Vigne'):
            dico_Ids[no_plte_res*initID]=no_plte_res
            for shp in s_vig:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=no_plte_res*initID)
    
        
        else:
            dico_Ids[no_plte_res*initID]=no_plte_res
            scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, sensor), id=no_plte_res*initID)
        
        print(no_plte_res)
        print(dico_Ids)
    
    dico_pltes_Ids[flag_couvert] = dico_Ids
        
    ###########RAJOUT des panneaux################
    #print(len(scene_out))
    if (agripv == True):
        scene_out_caribu += Shape(Translated(0, 0, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))

    pattern_caribu = (-(nb_plt_g+0.5)*distance_plante,-distance_plante/2,(nb_plt_d+0.5)*distance_plante,distance_plante/2)
    colored_scene = Calcul_Caribu_direct(scene_out_caribu, pattern_caribu, infini, dico_pltes_Ids)
    print(len(dico_pltes_Ids[flag_couvert]),pattern_caribu)
    return SceneWidget(colored_scene, size_world=75)


def cellule_analyse_AgriPV_direct():
    interact(Run_AgriPV_direct,
             agripv = widgets.Checkbox(
                 value=True,
                 description='AgriPV',
                 disabled=False,
                 indent=False
    ),             
             interpanel=widgets.FloatSlider(
                 value=0.,
                 min=1,
                 max=10,
                 step=5,
                 description='InterPanel',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
             ),             
             nb_plantes_caribu=widgets.IntSlider(
                 value=10,
                 min=1,
                 max=30,
                 step=5,
                 description='Nb Plantes',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='d',
             ),
             distance_plante=widgets.FloatSlider(
                 value=50.,
                 min=5.,
                 max=60.0,
                 step=5.,
                 description='InterPlantes (cm):',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
             ),
             panelsize=(10,50,10), angle_panel=(-90,90,10), height_panel=(0,50,10),
             flag_couvert = widgets.Dropdown(
                options=['Luzerne', 'Fétuque','Vigne', 'Sol'],
                value='Sol',
                description='Couvert :',
                disabled=False,
    ),
            infini = widgets.Checkbox(
        value=True,
        description='Couvert Infini',
        disabled=False,
        indent=False
    ));
    return
