#!/usr/bin/python3

import os
import sys
from PIL import Image
from pathlib import Path
import pathlib
import xml.etree.cElementTree as ET
# import time
# Time is here purely for debugging.

DecompMode = "null"

def is_pixel_alpha(pixel: tuple or int):
    pixel_value = pixel[3] if isinstance(pixel, tuple) else pixel
    return pixel_value == 0

def compileSheet():
    CharacterName = input("Please enter desired name for the character sheet: ")
    imagesLeft = 0

    # Variables to store the previous image to later.
    memoryX = 0
    memoryY = 0
    memoryMaxY = 0
    memoryMaxX = 0
    memoryW = 0
    memoryH = 0
    memoryCurrentY = 0
    memoryArray = []

    images = []
    path = input('Please enter path to images\n.png should be in lower case, images should follow the naming pattern "ANIM+NUMBER"\nfor example "Left1" for the first frame of the animation "Left". ')
    for p in Path(path).glob("**/*.png"):
        images.append(Image.open(str(p)))
        imagesLeft += 1
    # check to provide a more understandable error instead of the auto-generated ones down the line. V
    if imagesLeft == 0:
    	print("Error: No .png files detected. Make sure that .png is in lower case.")
    	sys.exit()

    doc = ET.Element("TextureAtlas", imagePath = f"{CharacterName}.png")
    doc.append(ET.Comment("Made using FNFanny Generator"))

    new_im = Image.new('RGBA', (10097, 10183))
    print("Please Wait...")
    while imagesLeft > 0:
        current = images[0]
        currentName = os.path.basename(current.filename)
        currentName = currentName.removesuffix('.png')

        if current in memoryArray:
            copycatIndex = memoryArray.index(current)
            copycat = memoryArray[copycatIndex]
            copycatName = os.path.basename(copycat.filename)
            copycatName = copycatName.removesuffix('.png')
            for SubTexture in doc.findall(f'./SubTexture/[@name="{copycatName}"]'):
                subX = SubTexture.get('x')
                subY = SubTexture.get('y')
                subWidth = SubTexture.get('width')
                subHeight = SubTexture.get('height')
                subFrameX = SubTexture.get('frameX')
                subFrameY = SubTexture.get('frameY')
                subFrameWidth = SubTexture.get('frameWidth')
                subFrameHeight = SubTexture.get('frameHeight')
                ET.SubElement(doc, "SubTexture", name=f"{currentName}", x=f"{subX}", y=f"{subY}", width=f"{subWidth}", height=f"{subHeight}", frameX=f"{subFrameX}", frameY=f"{subFrameY}", frameWidth=f"{subFrameWidth}", frameHeight=f"{subFrameHeight}").text
        else:
            memoryArray.append(current)
            width, height = current.size
            pixels = current.load()
            right = 0
            bottom = 0
            for y in reversed(range(0, height)):
                for x in reversed(range(0, width)):
                    if not is_pixel_alpha(pixels[x, y]):
                        if right == 0 or x + 1 > right:
                            right = x + 1
                        break
            for y in reversed(range(0, height)):
                for x in reversed(range(0, width)):
                    if not is_pixel_alpha(pixels[x, y]):
                        if bottom == 0 or y + 1 > bottom:
                            bottom = y + 1
                        break
            croppedBox = current.getbbox()
            current = current.crop(croppedBox)
            croppedWidth, croppedHeight = current.size
            right -= width
            bottom -= height
            # V has to be here in the order to not override itself  V
            new_im.paste(current, (memoryX, memoryY))
            ET.SubElement(doc, "SubTexture", name=f"{currentName}", x=f"{memoryX}", y=f"{memoryY}", width=f"{croppedWidth}", height=f"{croppedHeight}", frameX=f"{right}", frameY=f"{bottom}", frameWidth=f"{width}", frameHeight=f"{height}").text
            if memoryMaxY < memoryY + croppedHeight:
                memoryMaxY = memoryY + croppedHeight
            if memoryCurrentY < croppedHeight:
                memoryCurrentY = croppedHeight
            if memoryMaxX < memoryX + croppedWidth:
                memoryMaxX = memoryX + croppedWidth
            # Maximums to prevent issue where python cannot paste the image V
            if memoryX + croppedWidth <= 8192:
                memoryX = memoryX + croppedWidth
            elif memoryY + croppedHeight <= 8192:
                memoryX = 0
                memoryY = memoryY + memoryCurrentY
                memoryCurrentY = 0
            else:
                print("Error: Too many/big sprites to fit into a spritesheet, please consider downscaling the images and using a scaling modifier later in-engine..")
                sys.exit()
        imagesLeft -= 1
        images.pop(0)

    tree = ET.ElementTree(doc)
    ET.indent(tree, space="\t", level=0)
    with open(f"{CharacterName}.xml", "wb") as f:
        tree.write(f, encoding="utf-8", xml_declaration=True)
    # crop the image to not be as ridiculously large when unnecesarry.
    new_im = new_im.crop((0, 0, memoryMaxX, memoryMaxY))
    new_im.save(f"{CharacterName}.png")
    print("...Done!")

def decompileSheet():
    pathTool = input('Please enter path to .xml\n.xml and .png should be in lower case, .png and .xml should reside in the same directory with the same name. ')
    xmlSheet = Path(pathTool)
    # checks to provide more understandable errors instead of the auto-generated ones down the line. V
    if xmlSheet.is_file() == False:
    	print("Error: that file does not exist. Please check spelling")
    	sys.exit()
    elif pathTool.endswith(".xml") == False:
    	print("Error: No .xml files detected. Make sure that .xml is in lower case.")
    	sys.exit()
    # The parser needs to be here. V
    tree = ET.parse(pathTool)
    root = tree.getroot()
    # The parser needs to be here. ^
    pathTool = pathTool.removesuffix('.xml') + ".png"
    im = Image.open(pathTool)
    MemoryX = []
    MemoryY = []
    print("Please Wait...")
    for child in root.findall('SubTexture'):
        subName = child.get('name')
        subX = int(child.get('x'))
        subY = int(child.get('y'))
        subWidth = int(child.get('width'))
        subHeight = int(child.get('height'))
        # Check if frame variables are being used here.
        if child.get('frameX'):
            subFrameX = int(child.get('frameX'))
            subFrameY = int(child.get('frameY'))
            subFrameWidth = int(child.get('frameWidth'))
            subFrameHeight = int(child.get('frameHeight'))
        else:
            subFrameX = False
        rightcrop = subX + subWidth
        bottomcrop = subY + subHeight
        # Crops to sprite size. ^
        temp_im = im.crop((subX, subY, rightcrop, bottomcrop))
        path = pathlib.Path("./Output")
        path.mkdir(parents=True, exist_ok=True)
        # Check if frame variables are being used here.
        if subFrameX:
            new_im = Image.new('RGBA', (subFrameWidth, subFrameHeight))
            new_im.paste(temp_im, (-1 * subFrameX, -1 * subFrameY))
            new_im.save(f".//Output/{subName}.png")
        else:
            temp_im.save(f".//Output/{subName}.png")
    print("...Done!")
    	
# At the bottom to prevent definition errors. V
while DecompMode == "null":
    DecompMode = input("FNFanny Version 1.0\n-----------------------------------------\nDo you wish to compile (c) or decompile (d): ")
    if DecompMode == "c":
        compileSheet()
    elif DecompMode == "d":
        decompileSheet()
    else:
    # reloads the question instead of straight up quitting process.
        print("Invalid option. Please try again...")
        DecompMode = "null"
