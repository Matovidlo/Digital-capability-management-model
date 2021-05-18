# Keras NLP tutorial https://keras.io/examples/nlp/text_classification_from_scratch/
# A integer input for vocab indices.
inputs = tf.keras.Input(shape=(1,), dtype="string")
max_features = 20000
# Next, we add a layer to map those vocab indices into a space of dimensionality
# 'embedding_dim'.
x = layers.Embedding(max_features, embedding_dim)(inputs)
x = layers.Dropout(0.5)(x)

# Conv1D + global max pooling
x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
x = layers.GlobalMaxPooling1D()(x)

# We add a vanilla hidden layer:
x = layers.Dense(128, activation="relu")(x)
x = layers.Dropout(0.5)(x)

# We project onto a single unit output layer, and squash it with a sigmoid:
predictions = layers.Dense(1, activation="sigmoid", name="predictions")(x)

model = tf.keras.Model(inputs, predictions)

# Compile the model with binary crossentropy loss and an adam optimizer.
model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])


#todo: this is LSTM which is better
# Article from https://realpython.com/python-keras-text-classification/
model = keras.Sequential()
# Adding embedding layer
model.add(layers.LSTM(128, input_shape=(MAXLEN, chars)))
model.add(layers.RepeatVector(8))
for _ in range(num_layers):
    model.add(layers.LSTM(128, return_sequences=True))
# Previous model
# model.add(layers.Dense(10, input_dim=input_dimension, activation='relu'))
# Current model addition
model.add(layers.Dense(chars, activation='softmax'))
model.compile(loss='categorical_crossentropy',
              optimizer='adam', metrics=['accuracy'])

