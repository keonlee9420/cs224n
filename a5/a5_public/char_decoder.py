#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CS224N 2019-20: Homework 5
"""

import torch
import torch.nn as nn


class CharDecoder(nn.Module):
    def __init__(self, hidden_size, char_embedding_size=50, target_vocab=None):
        """ Init Character Decoder.

        @param hidden_size (int): Hidden size of the decoder LSTM
        @param char_embedding_size (int): dimensionality of character embeddings
        @param target_vocab (VocabEntry): vocabulary for the target language. See vocab.py for documentation.
        """
        super(CharDecoder, self).__init__()
        self.target_vocab = target_vocab
        self.charDecoder = nn.LSTM(char_embedding_size, hidden_size)
        self.char_output_projection = nn.Linear(hidden_size, len(self.target_vocab.char2id))
        self.decoderCharEmb = nn.Embedding(len(self.target_vocab.char2id), char_embedding_size,
                                           padding_idx=self.target_vocab.char_pad)
        self.softmax = nn.Softmax(dim=-1)
        self.criterion = nn.CrossEntropyLoss(ignore_index=self.target_vocab.char_pad , reduction='sum')

    def forward(self, input, dec_hidden=None):
        """ Forward pass of character decoder.

        @param input (Tensor): tensor of integers, shape (length, batch_size)
        @param dec_hidden (tuple(Tensor, Tensor)): internal state of the LSTM before reading the input characters. A tuple of two tensors of shape (1, batch, hidden_size)

        @returns scores (Tensor): called s_t in the PDF, shape (length, batch_size, self.vocab_size)
        @returns dec_hidden (tuple(Tensor, Tensor)): internal state of the LSTM after reading the input characters. A tuple of two tensors of shape (1, batch, hidden_size)
        """
        ### YOUR CODE HERE for part 2a
        ### TODO - Implement the forward pass of the character decoder.
        input_embedded = self.decoderCharEmb(input) # (length, batch_size, char_embedding_size)
        output, dec_hidden = self.charDecoder(input_embedded, dec_hidden)
        scores = self.char_output_projection(output)

        return scores, dec_hidden
        ### END YOUR CODE

    def train_forward(self, char_sequence, dec_hidden=None):
        """ Forward computation during training.

        @param char_sequence (Tensor): tensor of integers, shape (length, batch_size). Note that "length" here and in forward() need not be the same.
        @param dec_hidden (tuple(Tensor, Tensor)): initial internal state of the LSTM, obtained from the output of the word-level decoder. A tuple of two tensors of shape (1, batch_size, hidden_size)

        @returns The cross-entropy loss (Tensor), computed as the *sum* of cross-entropy losses of all the words in the batch.
        """
        ### YOUR CODE HERE for part 2b
        ### TODO - Implement training forward pass.
        ###
        ### Hint: - Make sure padding characters do not contribute to the cross-entropy loss. Check vocab.py to find the padding token's index.
        ###       - char_sequence corresponds to the sequence x_1 ... x_{n+1} (e.g., <START>,m,u,s,i,c,<END>). Read the handout about how to construct input and target sequence of CharDecoderLSTM.
        ###       - Carefully read the documentation for nn.CrossEntropyLoss and our handout to see what this criterion have already included:
        ###             https://pytorch.org/docs/stable/nn.html#crossentropyloss

        input = char_sequence[:-1] # (length-1, batch_size)
        output = char_sequence[1:] # (length-1, batch_size)
        scores, dec_hidden = self.forward(input, dec_hidden) # scores: (length-1, batch_size, self.vocab_size)
        loss_cross_entropy = self.criterion(scores.reshape([-1, scores.shape[-1]]), output.reshape(-1))

        return loss_cross_entropy
        ### END YOUR CODE

    def decode_greedy(self, initialStates, device, max_length=21):
        """ Greedy decoding
        @param initialStates (tuple(Tensor, Tensor)): initial internal state of the LSTM, a tuple of two tensors of size (1, batch_size, hidden_size)
        @param device: torch.device (indicates whether the model is on CPU or GPU)
        @param max_length (int): maximum length of words to decode

        @returns decodedWords (List[str]): a list (of length batch_size) of strings, each of which has length <= max_length.
                              The decoded strings should NOT contain the start-of-word and end-of-word characters.
        """

        ### YOUR CODE HERE for part 2c
        ### TODO - Implement greedy decoding.
        ### Hints:
        ###      - Use initialStates to get batch_size.
        ###      - Use target_vocab.char2id and target_vocab.id2char to convert between integers and characters
        ###      - Use torch.tensor(..., device=device) to turn a list of character indices into a tensor.
        ###      - You may find torch.argmax or torch.argmax useful
        ###      - We use curly brackets as start-of-word and end-of-word characters. That is, use the character '{' for <START> and '}' for <END>.
        ###        Their indices are self.target_vocab.start_of_word and self.target_vocab.end_of_word, respectively.
        
        # START_TOKEN = '{'
        # END_TOKEN = '}'
        START_TOKEN_INDEX = self.target_vocab.start_of_word
        END_TOKEN_INDEX = self.target_vocab.end_of_word
        batch_size = initialStates[0].shape[1]

        output_words = torch.zeros([max_length, batch_size], device=device) # (max_length, batch_size)
        current_char = torch.tensor([[START_TOKEN_INDEX] for i in range(batch_size)], device=device).t() # (length, batch_size), length = 1
        dec_hidden = initialStates

        for j in range(max_length):
            score, dec_hidden = self.forward(current_char, dec_hidden) # score: (length, batch_size, self.vocab_size)
            prob = self.softmax(score) # (length, batch_size, self.vocab_size)
            current_char = torch.argmax(prob, dim=-1) # (length, batch_size)
            output_words[j, :] = current_char

        decodedWords = []
        for b in range(batch_size):
            decodedWord = ''
            c_indices = output_words[:, b] # (max_length, )
            for c in c_indices:
                if c == END_TOKEN_INDEX:
                    break
                decodedWord += self.target_vocab.id2char[c.item()]
            decodedWords.append(decodedWord)

        return decodedWords
        ### END YOUR CODE

