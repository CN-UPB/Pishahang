# From https://gist.github.com/philwo/f3a8144e46168f23e40f291ffe92e63c

sudo apt install python3-dev python3-pip curl

pip3 install -U --user pip six numpy wheel setuptools mock 'future>=0.17.1'
pip3 install -U --user keras_applications --no-deps
pip3 install -U --user keras_preprocessing --no-deps

# Download Bazel
curl -Lo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/v1.1.0/bazelisk-linux-amd64
chmod +x /usr/local/bin/bazel

# Download TensorFlow 2.0:
curl -LO https://github.com/tensorflow/tensorflow/archive/v2.1.0.tar.gz
tar xvfz v2.1.0.tar.gz
rm v2.1.0.tar.gz
cd tensorflow-2.1.0

# Find out which Bazel version we need to build this release:
grep -r _TF_MAX_BAZEL_VERSION .

# Tell Bazelisk to build this version of TensorFlow with the matching release.
echo "0.29.1" > .bazelversion

# Verify that we use the correct Bazel version now:
bazel version

# Configure the build.
# When asked for the location of Python, make sure to enter /usr/bin/python3,
# otherwise it will use Python 2.x. For the rest of the questions, I just pressed
# enter to accept the defaults.
./configure

# Build TensorFlow:
bazel build --config=opt //tensorflow/tools/pip_package:build_pip_package
./bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg


# Install the package:
pip3 install --user /tmp/tensorflow_pkg/tensorflow-2.1.0-cp36-cp36m-linux_x86_64.whl

# Try it!
mkdir ~/tmp
cd ~/tmp
cat > hellotf.py <<'EOF'
#!/usr/bin/env python3

import tensorflow as tf
mnist = tf.keras.datasets.mnist

(x_train, y_train),(x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

model = tf.keras.models.Sequential([
  tf.keras.layers.Flatten(input_shape=(28, 28)),
  tf.keras.layers.Dense(128, activation='relu'),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(10, activation='softmax')
])

model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

model.fit(x_train, y_train, epochs=5)
model.evaluate(x_test, y_test)
EOF

python3 hellotf.py