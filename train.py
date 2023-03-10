import json
import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms

from projection_utils import get_corresponding_grid
from util import get_folder_paths, read_img_generator, read_input_map_generator
from model import Vertex2Image

load_pretrained = True
checkpoint_path = './checkpoint/epoch298.pt'
cuda = True
input_channels = 64

batch = 4
epoch = 300
resolution = (256,256)


with open("./vertex_init.json", "r") as lvf:
    vertex_feature = json.loads(lvf.read())

vertex_feature = torch.tensor(vertex_feature)

# vertex_feature = torch.rand(input_channels, 6890)

# list_vertex_feature = vertex_feature.numpy().tolist()
# with open("./vertex_init.json", "w") as lvf:
#     json.dump(list_vertex_feature, lvf)

if cuda:
    vertex_feature = vertex_feature.cuda()


model = Vertex2Image(vertex_feature, input_channels)
if load_pretrained:
    checkpoint = torch.load(checkpoint_path)
    model.load_state_dict(checkpoint['model_state_dict'])
    print("Load Checkpoint")

if cuda:
    model.cuda()
model.train()

if cuda:
    criterion = nn.L1Loss().cuda()
else:
    criterion = nn.L1Loss()

optimizer = optim.Adam(model.parameters(), lr=0.0001)
if load_pretrained:
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

if cuda:
    print("Model is loaded to CUDA")
else:
    print("Model is loaded to CPU")



# lr_scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.1, patience=5, verbose=True)
# lr_scheduler = optim.lr_scheduler.MultiStepLR(optimizer, milestones=[100,200,300,500,800], gamma=0.1)

# model.eval()


import numpy as np
import json
from PIL import Image
import glob


def get_folder_paths(folder="./data/"):
    dataset_folders = []
    for path in glob.glob(folder + "*"):
        dataset_folders.append(path)
    # dataset_folders = dataset_folders[0:5]
    # dataset_folders = [dataset_folders[1]]
    print("dataset paths: ", dataset_folders)
    return dataset_folders


def get_files_path(path):
    file_path = []
    for file in glob.glob(path):
        file_path.append(file)
    return file_path


def read_image(path):
    with Image.open(path, "r") as img:
        data = np.array(img)
    return data


def read_vertex(path):
    with open(path, "r") as jf:
        data = json.loads(jf.read())
    return data


def read_imgs(paths):
  imgs = []
  for file_path in glob.glob(paths):
    with Image.open(file_path) as img:
      img = np.array(img)
      img = np.array([img[:,:,0], img[:,:,1], img[:,:,2]])
      imgs.append(img)
  return np.array(imgs)


# def read_img_generator(paths):
#   for file_path in glob.glob(paths):
#     with Image.open(file_path) as img:
#       img = np.array(img)
#       img = np.array([img[:,:,0], img[:,:,1], img[:,:,2]])
#       yield img


def read_input_map(path):
  inputs = []
  with open(path, "r") as jf:
    data = json.loads(jf.read())
    inputs.append(data)
  return np.array(inputs)


# def read_input_map_generator(path):
#   with open(path, "r") as jf:
#     data = json.loads(jf.read())
#   for input in data:
#     yield input



norm = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
# select how many dataset you want to specify. Go into the function change it
dataset_folders = get_folder_paths()

all_loss = {}
# def train():
  # with autograd.detect_anomaly():
i = 0

# I am selecting just the first folder for training purpose
folder = dataset_folders[0]

# for some reason the SMPL misaligned after 250th image, so I just train the first 250 images
n_files = 250

gt_image = read_imgs(folder + "/images_256by256/*.png")
gt_image = torch.tensor(gt_image[0:250], dtype=torch.float32)

color_map = read_input_map(folder + "/color_inputs.json")
color_map = torch.tensor(color_map, dtype=torch.float32)
color_map = color_map.squeeze()[0:250]
color_map = norm(color_map)

vert_rot_map = read_input_map(folder + "/vert_rot.json")
vert_rot_map = torch.tensor(vert_rot_map, dtype=torch.float32)
vert_rot_map = vert_rot_map.squeeze()[0:250]

print("GT Image Shape: ", gt_image.shape)
print("Color Map Shape: ", color_map.shape)
print("Motion Map Shape: ", vert_rot_map.shape)

print("dataset is loaded")


for e in range(300,301):
    # n_files = len(get_files_path(folder + "/images_256by256/*.png"))

    total_losses = 0.
    for j in range(0, n_files, batch):
      # gt_image_batch = []
      # c_batch = []
      # v_batch = []

      # for n in range(batch):
      #   img = next(gt_image, None)
      #   c_map = next(color_map, None)
      #   v_map = next(vert_rot_map, None)
      #   if isinstance(img, type(None)) or isinstance(c_map, type(None)) or isinstance(v_map, type(None)):
      #     break

      #   gt_image_batch.append(img)
      #   c_batch.append(c_map)
      #   v_batch.append(v_map)
      
      # if len(gt_image_batch) != 0:
      #   gt_image_batch = np.array(gt_image_batch)
      #   c_batch = np.array(c_batch)
      #   v_batch = np.array(v_batch)

      #   gt_image_batch = torch.tensor(gt_image_batch, dtype=torch.float32)
      #   c_batch = torch.tensor(c_batch, dtype=torch.float32)
      #   c_batch = norm(c_batch)
      #   v_batch = torch.tensor(v_batch, dtype=torch.float32)
        # inputs = torch.cat((c_batch, torch.tensor(v_batch, dtype=torch.float32)), 1)

      gt_image_batch = gt_image[j : j + batch]
      c_batch = color_map[j : j + batch]
      v_batch = vert_rot_map[j : j + batch]

      if cuda:
        gt_image_batch = gt_image_batch.cuda()
        c_batch = c_batch.cuda()
        v_batch = v_batch.cuda()
        # inputs = inputs.cuda()

      optimizer.zero_grad()
      y = model(c_batch, v_batch)

      if j % 4 == 0:
        
        # inp = inputs[0].cpu().detach().numpy()
        # inp = vert_batch[0].cpu().numpy()
        # img = np.zeros(resolution)
        # for r, row in enumerate(inp):
        #   for c, col in enumerate(row):
        #     if np.isnan(col) == False:
        #       img[r][c] = 255
        # img = img.astype(np.uint8)
        # save_img = Image.fromarray(img).convert("L")
        # save_img.save(f"./output/epoch{e}_folder{i}_frame{j}_input.png")


        img = gt_image_batch[0].detach().cpu().numpy()
        cr = np.expand_dims(img[0], axis=2)
        cg = np.expand_dims(img[1], axis=2)
        cb = np.expand_dims(img[2], axis=2)
        img_reshape = np.concatenate((cr,cg,cb), 2)
        img_reshape = img_reshape.astype(np.uint8)
        save_img = Image.fromarray(img_reshape)
        save_img.save(f"./output/epoch{e}_folder{i}_frame{j}_gt.png")

        pred_img = y[0].detach().cpu().numpy()
        cr = np.expand_dims(pred_img[0], axis=2)
        cg = np.expand_dims(pred_img[1], axis=2)
        cb = np.expand_dims(pred_img[2], axis=2)
        img_reshape = np.concatenate((cr,cg,cb), 2)
        img_reshape = img_reshape.astype(np.uint8)
        save_img = Image.fromarray(img_reshape)
        save_img.save(f"./output/epoch{e}_folder{i}_frame{j}_pred.png")

      loss = criterion(y, gt_image_batch)
      # print("round: ", j, "loss: ", loss)
    
      total_losses += loss
      
      loss.backward()

      optimizer.step()

      if j == 248:
        print("Weight is saved at the checkpoint:", j)
        torch.save({
          'epoch': i,
          'model_state_dict': model.state_dict(),
          'optimizer_state_dict': optimizer.state_dict(),
          'loss': loss,
        }, f"./checkpoint/epoch{e}_folder{i}_frame_{j}.pt")
        
        name = f"epoch{e}_folder{i}_frame{j}"
        all_loss[name] = round(float(total_losses.cpu()) / 62, 5)
        total_losses = 0.
        # all_loss[name] = round(float(total_losses.cpu()) / 64, 5)
        # if j == 124:
        #   all_loss[name] = round(float(total_losses.cpu()) / 64, 5)
        # else:
        #   all_loss[name] = round(float(total_losses.cpu()) / (j / 84 * 21), 5)
      

    print("=====================================")  
    print("Total Loss Curve: ")
    for k in all_loss:
      print(k, all_loss[k])
    print("")

    # lr_scheduler.step(total_losses)
    # print("current lr rate: ", lr_scheduler._last_lr)
    # print("")