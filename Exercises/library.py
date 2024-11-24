from alinea.caribu.CaribuScene import CaribuScene
from alinea.caribu.sky_tools import GenSky, GetLight, Gensun, GetLightsSun
from openalea.plantgl.all import *
from pgljupyter import SceneWidget
from numpy import arange, random
import matplotlib.pyplot as plt
from openalea.lpy import Lsystem
from ipywidgets import interact, interactive, fixed, interact_manual, widgets
from math import ceil, floor

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


def Run_AgriPV_diffus(agripv = True, distance=30, distance_plante = 10, panelsize = 10, angle_panel = 40, height_panel = 0, flag_couvert = 'Luzerne', infini = True):
    def Calcul_Caribu_diffus(scene, pattern_caribu, infini, dico_IDs):
        # ciel
        sky_string = GetLight.GetLight(GenSky.GenSky()(1, 'soc', 4, 5))  # (Energy, soc/uoc, azimuts, zenits)

        sky = []
        for string in sky_string.split('\n'):
            if len(string) != 0:
                string_split = string.split(' ')
                t = tuple((float(string_split[0]), tuple((float(string_split[1]), float(string_split[2]), float(string_split[3])))))
                sky.append(t)

        c_scene = CaribuScene(scene=scene, light=sky, pattern=pattern_caribu)
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
    #print(len(s_vig))

    scene_asso = s_luz + s_fet
    # Visualisation of the association
    scene_out, scene_out_caribu = Scene(),Scene()

    #for shp in scene_asso:
    #    if shp.id <= 1000:  # Fetuque
    #        scene_out += Shape(Translated(distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
    #    else:  # Luzerne
    #        scene_out += Shape(Translated(-distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)

    #distance_plante = 10.
    initID = 1000
    distance = distance*100 #conversion en cm
    nb_plantes = round(2.*distance/distance_plante)+1
    nb_plantes_caribu = round(distance/distance_plante)+1
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
    for num_plante in range(0,nb_plantes_caribu):
        if (flag_couvert=='Luzerne'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)

        elif (flag_couvert=='Fétuque'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante,shp.geometry)), shp.appearance, id=num_plante*initID)
    
        elif (flag_couvert=='Vigne'):
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            for shp in s_vig:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
    
        
        else:
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
            elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
                
            #scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, sensor), id=num_plante*initID)
        dico_pltes_Ids[flag_couvert] = dico_Ids
        no_plte_res += 1
    ###########RAJOUT des panneaux################
    #print(len(scene_out))
    if (agripv == True):
        scene_out_caribu += Shape(Translated(0, 0, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        scene_out_caribu += Shape(Translated(0, distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #if (distance/distance_plante%2==0):
        #    scene_out += Shape(Translated(0, -distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #    scene_out += Shape(Translated(0, +distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #else:
        #    scene_out += Shape(Translated(0, (-distance+distance_plante)/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #    scene_out += Shape(Translated(0, (+distance/2+distance_plante)/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
                
            #for shp in s_fet:
            #    scene_out += Shape(Translated(-distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
            #    scene_out += Shape(Translated(+distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
    pattern_caribu = (-(distance-(nb_plantes_caribu-1)*distance_plante)/2,-distance_plante/2,(distance-(nb_plantes_caribu-1)*distance_plante)/2,distance_plante/2)
    colored_scene = Calcul_Caribu_diffus(scene_out_caribu, pattern_caribu, infini, dico_pltes_Ids)
    print(len(dico_pltes_Ids[flag_couvert]),pattern_caribu)
    return SceneWidget(colored_scene, size_world=75)

def cellule_analyse_AgriPV_diffus():
    # # Makes Lsystem for association
    interact(Run_AgriPV_diffus,
             agripv = widgets.Checkbox(
                 value=True,
                 description='AgriPV',
                 disabled=False,
                 indent=False
    ),             
             distance=widgets.FloatSlider(
                 value=5.,
                 min=0,
                 max=10.0,
                 step=0.1,
                 description='InterPV (m):',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
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
                value='Luzerne',
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



    #############PARTIE POUR UNE DIRECTION DU SOLEIL############################
    
def Run_AgriPV_direct(agripv = True, distance=30, nb_plantes_caribu = 10, panelsize = 10, angle_panel = 40, height_panel = 0, flag_couvert = 'Luzerne', infini = True, hour = 12):
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

        c_scene = CaribuScene(scene=scene, light=[sun], pattern=(BoundingBox(scene).getXMin(), BoundingBox(scene).getYMin(), BoundingBox(scene).getXMax(), BoundingBox(scene).getYMax()))
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
    #print(len(s_vig))

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
    distance = distance*100 #conversion en cm
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
    ########plangtes d'un cote des panneaux########################
    #for num_plante in range(0,nb_plantes_caribu):
    for num_plante in range(nb_plt_g):
        if (flag_couvert=='Luzerne'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                #    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                #    nb_plt_g +=1
                #    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                
        elif (flag_couvert=='Fétuque'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante,shp.geometry)), shp.appearance, id=num_plante*initID)
    
        elif (flag_couvert=='Vigne'):
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            for shp in s_vig:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
    
        
        else:
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
            elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
                
            #scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, sensor), id=num_plante*initID)
        no_plte_res += 1

    ########plantes de l'autre cote des panneaux########################
    #for num_plante in range(0,nb_plantes_caribu):
    for num_plante in range(nb_plt_d):
        if (flag_couvert=='Luzerne'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_luz:
                scene_out_caribu += Shape(Translated(0, num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                #    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                #    nb_plt_g +=1
                #    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                
        elif (flag_couvert=='Fétuque'):
            #if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            azimut_plante = random.random()*3.14
            for shp in s_fet:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante,shp.geometry)), shp.appearance, id=num_plante*initID)
    
        elif (flag_couvert=='Vigne'):
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            for shp in s_vig:
                if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                    scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                    scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), azimut_plante, shp.geometry)), shp.appearance, id=num_plante*initID)
                    
                #if (distance/distance_plante%2==0):
                #    scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
                #else:
                #    scene_out += Shape(Translated(0, -distance+(num_plante+1/2)*distance_plante, 0, shp.geometry), shp.appearance, id=num_plante*initID)
    
        
        else:
            #if ((-distance+num_plante*distance_plante>=-distance/2) and (-distance+num_plante*distance_plante<=distance/2)):
            dico_Ids[num_plante*initID]=num_plante+1
            if ((-distance/2+num_plante*distance_plante>=-distance/2) and (-distance/2+num_plante*distance_plante<=0)):
                scene_out_caribu += Shape(Translated(0, -num_plante*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
            elif ((-distance/2+num_plante*distance_plante>0) and (-distance/2+num_plante*distance_plante<=+distance/2)):
                scene_out_caribu += Shape(Translated(0, (nb_plantes_caribu-num_plante)*distance_plante, 0, AxisRotated((0,0,1), 0, sensor)), shp.appearance, id=num_plante*initID)
                
            #scene_out += Shape(Translated(0, -distance+num_plante*distance_plante, 0, sensor), id=num_plante*initID)
        no_plte_res += 1
    dico_pltes_Ids[flag_couvert] = dico_Ids
        
    print('distance apres', distance)
    distance = (nb_plt_g + nb_plt_d - 1)*distance_plante
    ###########RAJOUT des panneaux################
    #print(len(scene_out))
    if (agripv == True):
        scene_out_caribu += Shape(Translated(0, 0, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #scene_out_caribu += Shape(Translated(0, distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #if (distance/distance_plante%2==0):
        #    scene_out += Shape(Translated(0, -distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #    scene_out += Shape(Translated(0, +distance/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #else:
        #    scene_out += Shape(Translated(0, (-distance+distance_plante)/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
        #    scene_out += Shape(Translated(0, (+distance/2+distance_plante)/2, height_panel, AxisRotated((1,0,0), angle_panel*3.14/180,panel)))
                
            #for shp in s_fet:
            #    scene_out += Shape(Translated(-distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
            #    scene_out += Shape(Translated(+distance/2, 0, 0, shp.geometry), shp.appearance, id=shp.id)
    pattern_caribu = (-(distance-(nb_plantes_caribu-1)*distance_plante)/2,-distance_plante/2,(distance-(nb_plantes_caribu-1)*distance_plante)/2,distance_plante/2)
    colored_scene = Calcul_Caribu_direct(scene_out_caribu, pattern_caribu, infini, dico_pltes_Ids)
    print(len(dico_pltes_Ids[flag_couvert]),pattern_caribu)
    return SceneWidget(colored_scene, size_world=75)


def cellule_analyse_AgriPV_direct():
    # # Makes Lsystem for association
    interact(Run_AgriPV_direct, 
             agripv = widgets.Checkbox(
                 value=True,
                 description='AgriPV',
                 disabled=False,
                 indent=False
    ),
             distance=widgets.FloatSlider(
                 value=0.3,
                 min=0,
                 max=10.0,
                 step=0.1,
                 description='InterPV (m):',
                 disabled=False,
                 continuous_update=False,
                 orientation='horizontal',
                 readout=True,
                 readout_format='.1f',
             ),
             distance_plante=widgets.FloatSlider(
                 value=10.,
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
                value='Luzerne',
                description='Couvert :',
                disabled=False,
    ),
             hour = (6,18,1),
            infini = widgets.Checkbox(
        value=True,
        description='Couvert Infini',
        disabled=False,
        indent=False
    ));
    return
