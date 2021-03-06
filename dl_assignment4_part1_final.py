# -*- coding: utf-8 -*-
"""DL_assignment4_part1_final.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iBrBcWEn9stUarnDVMDHLkMQlYzAaPBO
"""

import pandas as pd
from google.colab import drive
import torchvision.models as models
from torch.utils.data import Dataset,DataLoader
from torchvision import transforms,utils
import os
import matplotlib.pyplot as plt
import cv2
import pickle
from google.colab.patches import cv2_imshow
import torch
import torch.nn.functional as F
import numpy as np
import torch
from torch.utils.data import DataLoader,Dataset
import torchvision.transforms as T
from nltk.translate.bleu_score import sentence_bleu
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import torchvision.models as models
from torch.utils.data import DataLoader,Dataset
import torchvision.transforms as T

drive.mount('gdrive',force_remount=True)
training_captions=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Train/train_captions.pkl')
validation_captions=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Val/val_captions.pkl')
testing_captions=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Test/test_captions.pkl')
# vgg=models.vgg19_bn(pretrained=True,progress=True)

train_data=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4/DL_ASS4_1_TRAIN.pkl')
val_data=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4/DL_ASS4_1_VALID.pkl')
test_data=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4/DL_ASS4_1_TEST.pkl')

transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            # transforms.RandomCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406),(0.229, 0.224, 0.225)),
        ]
    )

!python -m spacy download en

import os  # when loading file paths
import pandas as pd  # for lookup in annotation file
import spacy  # for tokenizer
import torch
from torch.nn.utils.rnn import pad_sequence  # pad batch
from torch.utils.data import DataLoader, Dataset
from PIL import Image  # Load img
import torchvision.transforms as transforms

import numpy as np

spacy_eng = spacy.load("en")


class Vocabulary:
    def __init__(self, freq_threshold):
        self.itos = {0: "<PAD>", 1: "<SOS>", 2: "<EOS>", 3: "<UNK>"}
        self.stoi = {"<PAD>": 0, "<SOS>": 1, "<EOS>": 2, "<UNK>": 3}
        self.freq_threshold = freq_threshold

    def __len__(self):
        return len(self.itos)

    @staticmethod
    def tokenizer_eng(text):
        return [tok.text.lower() for tok in spacy_eng.tokenizer(text)]

    def build_vocabulary(self, sentence_list):
        frequencies = {}
        idx = 4

        for sentence in sentence_list:
            for word in self.tokenizer_eng(sentence):
                if word not in frequencies:
                    frequencies[word] = 1

                else:
                    frequencies[word] += 1

                if frequencies[word] == self.freq_threshold:
                    self.stoi[word] = idx
                    self.itos[idx] = word
                    idx += 1

    def numericalize(self, text):
        tokenized_text = self.tokenizer_eng(text)

        return [
            self.stoi[token] if token in self.stoi else self.stoi["<UNK>"]
            for token in tokenized_text
        ]


class InputDataset(Dataset):
    def __init__(self, root_dir, captions_file, transform=None, freq_threshold=1):
        self.root_dir = root_dir
        self.df = pd.read_csv(captions_file)
        self.transform = transform
        print(self.df)
        # Get img, caption columns
        self.imgs = self.df["images"]
        self.captions = self.df["captions"]

        # Initialize vocabulary and build vocab
        self.vocab = Vocabulary(freq_threshold)
        self.vocab.build_vocabulary(self.captions.tolist())
        self.max_len=0
        for t,_ in self.vocab.stoi.items():
          if len(t) > self.max_len:
            self.max_len = len(t)


    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        caption = self.captions[index]
        img_id = self.imgs[index]
        img = Image.open(os.path.join(self.root_dir, img_id)).convert("RGB")

        if self.transform is not None:
            img = self.transform(img)

        numericalized_caption = [self.vocab.stoi["<SOS>"]]
        numericalized_caption += self.vocab.numericalize(caption)
        numericalized_caption.append(self.vocab.stoi["<EOS>"])
        pad_list = [self.vocab.stoi["<PAD>"]] * (38 - len(numericalized_caption))
        for p in range(len(pad_list)):
          numericalized_caption.append(pad_list[p])

        return img, torch.tensor(numericalized_caption)


def get_loader(
    transform,
    batch_size=32,
    num_workers=0,
    shuffle=True,
):

    pad_idx = train_dataset.vocab.stoi["<PAD>"]
    print("here1")
    # c= MyCollate(pad_idx=pad_idx)
    print("here2")
    loader = DataLoader(
        dataset=train_dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        shuffle=shuffle, pin_memory=True,
    )

    return loader

root_folder="/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Train/Images/"
annotation_file="/content/gdrive/MyDrive/DL/assignment4_new/captions.txt"
train_dataset = InputDataset(root_folder, annotation_file, transform=transform)

data_loader = get_loader(
        transform=transform,
        num_workers=4,
        batch_size=4
    )

vocab_size = len(train_dataset.vocab)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class EncoderCNN(nn.Module):
    def __init__(self):
        super(EncoderCNN, self).__init__()
        resnet = models.vgg19_bn(pretrained=True,progress=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-2]
        self.resnet = nn.Sequential(*modules)
        

    def forward(self, images):
        features = self.resnet(images)                                    #(batch_size,2048,7,7)
        # print(features.shape)
        features = features.permute(0, 2, 3, 1)                           #(batch_size,7,7,2048)
        features = features.view(features.size(0), -1, features.size(-1)) #(batch_size,49,2048)
        return features

#Bahdanau Attention
class Attention(nn.Module):
    def __init__(self, encoder_dim,decoder_dim,attention_dim):
        super(Attention, self).__init__()
        
        self.attention_dim = attention_dim
        
        self.W = nn.Linear(decoder_dim,attention_dim)
        self.U = nn.Linear(encoder_dim,attention_dim)
        
        self.A = nn.Linear(attention_dim,1)
        
        
        
        
    def forward(self, features, hidden_state):
        u_hs = self.U(features)     #(batch_size,num_layers,attention_dim)
        w_ah = self.W(hidden_state) #(batch_size,attention_dim)
        
        combined_states = torch.tanh(u_hs + w_ah.unsqueeze(1)) #(batch_size,num_layers,attemtion_dim)
        
        attention_scores = self.A(combined_states)         #(batch_size,num_layers,1)
        attention_scores = attention_scores.squeeze(2)     #(batch_size,num_layers)
        
        
        alpha = F.softmax(attention_scores,dim=1)          #(batch_size,num_layers)
        
        attention_weights = features * alpha.unsqueeze(2)  #(batch_size,num_layers,features_dim)
        attention_weights = attention_weights.sum(dim=1)   #(batch_size,num_layers)
        
        return alpha,attention_weights

#Attention Decoder
class DecoderRNN(nn.Module):
    def __init__(self,embed_size, vocab_size, attention_dim,encoder_dim,decoder_dim,drop_prob=0.3):
        super().__init__()
        
        #save the model param
        self.vocab_size = vocab_size
        self.attention_dim = attention_dim
        self.decoder_dim = decoder_dim
        
        self.embedding = nn.Embedding(vocab_size,embed_size)
        self.attention = Attention(encoder_dim,decoder_dim,attention_dim)
        
        
        self.init_h = nn.Linear(encoder_dim, decoder_dim)  
        self.init_c = nn.Linear(encoder_dim, decoder_dim)  
        self.lstm_cell = nn.LSTMCell(embed_size+encoder_dim,decoder_dim,bias=True)
        self.f_beta = nn.Linear(decoder_dim, encoder_dim)
        
        
        self.fcn = nn.Linear(decoder_dim,vocab_size)
        self.drop = nn.Dropout(drop_prob)
        
        
    
    def forward(self, features, captions):
        
        #vectorize the caption
        embeds = self.embedding(captions)
        
        # Initialize LSTM state
        h, c = self.init_hidden_state(features)  # (batch_size, decoder_dim)
        
        #get the seq length to iterate
        seq_length = len(captions[0])-1 #Exclude the last one
        batch_size = captions.size(0)
        num_features = features.size(1)
        
        preds = torch.zeros(batch_size, seq_length, self.vocab_size).to(device)
        alphas = torch.zeros(batch_size, seq_length,num_features).to(device)
                
        for s in range(seq_length):
            alpha,context = self.attention(features, h)
            lstm_input = torch.cat((embeds[:, s], context), dim=1)
            h, c = self.lstm_cell(lstm_input, (h, c))
                    
            output = self.fcn(self.drop(h))
            
            preds[:,s] = output
            alphas[:,s] = alpha  
        
        
        return preds, alphas
    
    def generate_caption(self,features,max_len=20,vocab=None):
        # Inference part
        # Given the image features generate the captions
        
        batch_size = features.size(0)
        h, c = self.init_hidden_state(features)  # (batch_size, decoder_dim)
        
        alphas = []
        
        #starting input
        word = torch.tensor(vocab.stoi['<SOS>']).view(1,-1).to(device)
        embeds = self.embedding(word)

        
        captions = []
        
        for i in range(max_len):
            alpha,context = self.attention(features, h)
            
            
            #store the apla score
            alphas.append(alpha.cpu().detach().numpy())
            
            lstm_input = torch.cat((embeds[:, 0], context), dim=1)
            h, c = self.lstm_cell(lstm_input, (h, c))
            output = self.fcn(self.drop(h))
            output = output.view(batch_size,-1)
        
            
            #select the word with most val
            predicted_word_idx = output.argmax(dim=1)
            
            #save the generated word
            captions.append(predicted_word_idx.item())
            
            #end if <EOS detected>
            if vocab.itos[predicted_word_idx.item()] == "<EOS>":
                break
            
            #send generated word as the next caption
            embeds = self.embedding(predicted_word_idx.unsqueeze(0))
        
        #covert the vocab idx to words and return sentence
        return [vocab.itos[idx] for idx in captions],alphas
    
    
    def init_hidden_state(self, encoder_out):
        mean_encoder_out = encoder_out.mean(dim=1)
        h = self.init_h(mean_encoder_out)  # (batch_size, decoder_dim)
        c = self.init_c(mean_encoder_out)
        return h, c

class EncoderDecoder(nn.Module):
    def __init__(self,embed_size, vocab_size, attention_dim,encoder_dim,decoder_dim,drop_prob=0.3):
        super().__init__()
        self.encoder = EncoderCNN()
        self.decoder = DecoderRNN(
            embed_size=embed_size,
            vocab_size = len(train_dataset.vocab),
            attention_dim=attention_dim,
            encoder_dim=encoder_dim,
            decoder_dim=decoder_dim
        )
        
    def forward(self, images, captions):
        features = self.encoder(images)
        outputs = self.decoder(features, captions)
        return outputs

#Hyperparams
embed_size=300
vocab_size = len(train_dataset.vocab)
attention_dim=256
encoder_dim=512
decoder_dim=512
learning_rate = 3e-4
#init model
model = EncoderDecoder(
    embed_size=300,
    vocab_size = len(train_dataset.vocab),
    attention_dim=256,
    encoder_dim=512,
    decoder_dim=512
).to(device)

criterion = nn.CrossEntropyLoss(ignore_index=train_dataset.vocab.stoi["<PAD>"])
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

def save_model(model,num_epochs):
    model_state = {
        'num_epochs':num_epochs,
        'embed_size':embed_size,
        'vocab_size':len(train_dataset.vocab),
        'attention_dim':attention_dim,
        'encoder_dim':encoder_dim,
        'decoder_dim':decoder_dim,
        'state_dict':model.state_dict()
    }

    torch.save(model_state,'attention_model_state.pth')

import matplotlib.pyplot as plt
def show_image(img, title=None):
    """Imshow for Tensor."""
    
    #unnormalize 
    img[0] = img[0] * 0.229
    img[1] = img[1] * 0.224 
    img[2] = img[2] * 0.225 
    img[0] += 0.485 
    img[1] += 0.456 
    img[2] += 0.406
    
    img = img.numpy().transpose((1, 2, 0))
    
    
    plt.imshow(img)
    if title is not None:
        plt.title(title)
    plt.pause(0.001)  # pause a bit so that plots are updated

num_epochs = 30
print_every = 100

for epoch in range(1,num_epochs+1):   
    for idx, (image, captions) in enumerate(iter(data_loader)):
        image,captions = image.to(device),captions.to(device)

        # Zero the gradients.
        optimizer.zero_grad()

        # Feed forward
        outputs,attentions = model(image, captions)

        # Calculate the batch loss.
        targets = captions[:,1:]
        loss = criterion(outputs.view(-1, vocab_size), targets.reshape(-1))
        
        # Backward pass.
        loss.backward()

        # Update the parameters in the optimizer.
        optimizer.step()

        if (idx+1)%print_every == 0:
            print("Epoch: {} loss: {:.5f}".format(epoch,loss.item()))
            
            
            #generate the caption
            model.eval()
            with torch.no_grad():
                dataiter = iter(data_loader)
                img,_ = next(dataiter)
                features = model.encoder(img[0:1].to(device))
                caps,alphas = model.decoder.generate_caption(features,vocab=train_dataset.vocab)
                caption = ' '.join(caps)
                show_image(img[0],title=caption)
                
            model.train()
        
    #save the latest model
    save_model(model,epoch)

m = torch.load("/content/attention_model_state.pth")
m['state_dict']

#load model
from google.colab.patches import cv2_imshow
model.load_state_dict(torch.load("/content/attention_model_state.pth")['state_dict'])
# model.eval()
#generate caption
def get_caps_from(features_tensors):
    #generate the caption
    model.eval()
    with torch.no_grad():
        features = model.encoder(features_tensors.to(device))
        caps,alphas = model.decoder.generate_caption(features,vocab=train_dataset.vocab)
        caption = ' '.join(caps)
        # show_image(features_tensors[0],title=caption)
    
    return caps,alphas

#Show attention
def plot_attention(img, result, attention_plot):
    #untransform
    img[0] = img[0] * 0.229
    img[1] = img[1] * 0.224 
    img[2] = img[2] * 0.225 
    img[0] += 0.485 
    img[1] += 0.456 
    img[2] += 0.406
    
    img = img.numpy().transpose((1, 2, 0))
    temp_image = img

    fig = plt.figure(figsize=(15, 15))

    len_result = len(result)
    for l in range(len_result):
        temp_att = attention_plot[l].reshape(7,7)
        
        ax = fig.add_subplot(len_result//2,len_result//2, l+1)
        ax.set_title(result[l])
        img = ax.imshow(temp_image)
        ax.imshow(temp_att, cmap='gray', alpha=0.7, extent=img.get_extent())
        

    plt.tight_layout()
    plt.show()

dataiter = iter(data_loader)
images,_ = next(dataiter)

img = images[0].detach().clone()
img1 = images[0].detach().clone()
caps,alphas = get_caps_from(img.unsqueeze(0))
print(caps)
plot_attention(img1, caps, alphas)

dataiter = iter(data_loader)
images,_ = next(dataiter)

img = images[0].detach().clone()
img1 = images[0].detach().clone()
caps,alphas = get_caps_from(img.unsqueeze(0))
print(caps)
plot_attention(img1, caps, alphas)

dataiter = iter(data_loader)
images,_ = next(dataiter)

img = images[0].detach().clone()
img1 = images[0].detach().clone()
caps,alphas = get_caps_from(img.unsqueeze(0))
print(caps)
plot_attention(img1, caps, alphas)

dataiter = iter(data_loader)
images,_ = next(dataiter)

img = images[0].detach().clone()
img1 = images[0].detach().clone()
caps,alphas = get_caps_from(img.unsqueeze(0))
print(caps)
plot_attention(img1, caps, alphas)

dataiter = iter(data_loader)
images,_ = next(dataiter)

img = images[0].detach().clone()
img1 = images[0].detach().clone()
caps,alphas = get_caps_from(img.unsqueeze(0))
print(caps)
plot_attention(img1, caps, alphas)

#for validation data
from nltk.translate.bleu_score import sentence_bleu
val_dir = "/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Val/Images"
val_data['file_names']
for i in range(len(val_data['file_names'])):
  if i <3:
    img = Image.open(os.path.join(val_dir, val_data['file_names'][i])).convert("RGB")
    img = transform(img)
    caps , _ = get_caps_from(img.unsqueeze(0))
    actual_captions = val_data['captions'][val_data['file_names'][i]]
    print("caption generated->" ,caps)
    print("actual captiosn -> ",actual_captions)
    print("bleu score - 1",sentence_bleu(actual_captions, caps,weights=[1,0,0,0]))
    print("bleu score - 2",sentence_bleu(actual_captions, caps,weights=[.5,0.5,0,0]))
    print("bleu score - 3",sentence_bleu(actual_captions, caps,weights=[.33,0.33,0.33,0.33]))
    print("bleu score - 4",sentence_bleu(actual_captions, caps,weights=[.25,0.25,0.25,0.25]))
    print("########################")

validation_data=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4/DL_ASS4_1_VALID.pkl')
testing_data=pd.read_pickle('/content/gdrive/MyDrive/DL/assignment4/DL_ASS4_1_TEST.pkl')

bleu_1_valid=0
bleu_2_valid=0
bleu_3_valid=0
bleu_4_valid=0
def form_sentences(caption_list):
    modified_caption_list=[]
    for sentence in caption_list:
        modified_caption_list.append(sentence.split(' '))
    return modified_caption_list

val_transform = transforms.Compose(
        [
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            # transforms.RandomCrop((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406),(0.229, 0.224, 0.225)),
        ]
    )
for i in range(len(validation_data['images'])):
    references=form_sentences(validation_data['captions'][validation_data['file_names'][i]])
    image=val_transform(validation_data['images'][i])
    candidate , _ = get_caps_from(image.unsqueeze(0))
    bleu_1_valid+=sentence_bleu(references,candidate,weights=(1,0,0,0))
    bleu_2_valid+=sentence_bleu(references,candidate,weights=(0.5,0.5,0,0))
    bleu_3_valid+=sentence_bleu(references,candidate,weights=(0.33,0.33,0.33,0))
    bleu_4_valid+=sentence_bleu(references,candidate,weights=(0.25,0.25,0.25,0.25))
bleu_1_test=0
bleu_2_test=0
bleu_3_test=0
bleu_4_test=0
for i in range(len(testing_data['images'])):
    references=form_sentences(testing_data['captions'][testing_data['file_names'][i]])
    image=val_transform(testing_data['images'][i])
    candidate , _ = get_caps_from(image.unsqueeze(0))
    bleu_1_test+=sentence_bleu(references,candidate,weights=(1,0,0,0))
    bleu_2_test+=sentence_bleu(references,candidate,weights=(0.5,0.5,0,0))
    bleu_3_test+=sentence_bleu(references,candidate,weights=(0.33,0.33,0.33,0))
    bleu_4_test+=sentence_bleu(references,candidate,weights=(0.25,0.25,0.25,0.25))

bleu_4_test/1000

#for testing data 
from nltk.translate.bleu_score import sentence_bleu
test_dir = "/content/gdrive/MyDrive/DL/assignment4_new/Show Attend and Tell complete Dataset/Data/Test/Images"
test_data['file_names']
for i in range(len(test_data['file_names'])):
  if i <3:
    img = Image.open(os.path.join(test_dir, test_data['file_names'][i])).convert("RGB")
    img = transform(img)
    caps , _ = get_caps_from(img.unsqueeze(0))
    actual_captions = val_data['captions'][val_data['file_names'][i]]
    # print("caption generated->" ,caps)
    # print("actual captiosn -> ",actual_captions)
    print("bleu score - 1",sentence_bleu(actual_captions, caps,weights=[1,0,0,0]))
    print("bleu score - 2",sentence_bleu(actual_captions, caps,weights=[.5,0.5,0,0]))
    print("bleu score - 3",sentence_bleu(actual_captions, caps,weights=[.33,0.33,0.33,0.33]))
    print("bleu score - 4",sentence_bleu(actual_captions, caps,weights=[.25,0.25,0.25,0.25]))
    print("########################")

cv2_imshow(train_data['images'][0])