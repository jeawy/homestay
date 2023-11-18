#! -*- coding:utf-8 -*-
from colour import Color
from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
import pdb
import uuid


def getcolors(startcolor, endcolor, steps=50):
    # 获取线性渐变颜色值rgb格式
    startcolor = Color(startcolor)
    colors = list(startcolor.range_to(Color(endcolor), steps))
    result = [[round(rgb,2) for rgb in color.rgb] for color in colors]
    return result
 
def plot_color_gradients(cmap_category, cmap_list):
    # Create figure and adjust figure height to number of colormaps
    
    gradient = np.linspace(0, 1, 90) 
    gradient = np.vstack((gradient, gradient)) 
    nrows = len(cmap_list)
    figh = 0.35 + 0.15 + (nrows + (nrows-1)*0.1)*0.22 
    fig, axs = plt.subplots(nrows=nrows, figsize=(6.4, figh))
    fig.subplots_adjust(top=1-.35/figh, bottom=.15/figh, left=0.2, right=0.99)
 
    for ax, cmap_name in zip(axs, cmap_list): 
        im = ax.imshow(gradient, aspect='auto', cmap=cmap_name)
        colors = im.cmap(im.norm(np.unique(gradient)))
        if cmap_name == "Reds":
            for color in colors:
                # 颜色值转换为255格式
                print([int(255 * item) for item in color[:3]])
        
            print(len(colors) )
        ax.text(-.01, .5, cmap_name, va='center', ha='right', fontsize=10,
                transform=ax.transAxes)

    # Turn off *all* ticks & spines, not just the ones with colormaps.
    for ax in axs:
        ax.set_axis_off()


    
def test():
    '''
    cmaps = [ 
            ('Sequential', [
                'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']),
            ('Sequential (2)', [
                'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                'hot', 'afmhot', 'gist_heat', 'copper']),
             ]

    '''
    cmaps = [   ('Sequential', [ 'Reds',  'YlOrBr' ]),  ]
    for cmap_category, cmap_list in cmaps:
        print(cmap_category)
        plot_color_gradients(cmap_category, cmap_list)

    plt.show()

def getfilenames(filepath):
    onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]
    print(onlyfiles)
    return onlyfiles

def getnos():
    result=[]
    for i in range(0, 1000):
        card = str(uuid.uuid4()).replace("-", "").upper()[4:16]
        if card not in result:
            print(card)
            result.append(card)
    
    print(len(result))


if __name__== "__main__":
    #getfilenames("C:\projects\py3\django2.2\property\community")
    getnos()