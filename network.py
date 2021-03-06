import tensorflow as tf


def generator(z, y=None, reuse=False, is_training=True):
    with tf.variable_scope('generator', reuse=reuse):
        alpha = 0.2
        n_filter = 512
        n_kernel = 4
        w_init = tf.contrib.layers.xavier_initializer()

        # 0. concatenate inputs
        # z: [batch size, 100], y: [batch size, 10]
        if y is not None:
            inputs = tf.concat([z, y], axis=1)
        else:
            inputs = z

        # 1. reshape z-vector to fit as 2d shape image with fully connected layer
        l1 = tf.layers.dense(inputs, units=3 * 3 * n_filter, kernel_initializer=w_init)
        l1 = tf.reshape(l1, shape=[-1, 3, 3, n_filter])
        l1 = tf.maximum(alpha * l1, l1)

        # 2. layer2 - [batch size, 3, 3, 512] ==> [batch size, 7, 7, 512]
        l2 = tf.layers.conv2d_transpose(l1, filters=n_filter // 2, kernel_size=3, strides=2, padding='valid',
                                        kernel_initializer=w_init)
        l2 = tf.layers.batch_normalization(l2, training=is_training)
        l2 = tf.maximum(alpha * l2, l2)

        # 3. layer3 - [batch size, 7, 7, 256] ==> [batch size, 14, 14, 128]
        l3 = tf.layers.conv2d_transpose(l2, filters=n_filter // 4, kernel_size=n_kernel, strides=2, padding='same',
                                        kernel_initializer=w_init)
        l3 = tf.layers.batch_normalization(l3, training=is_training)
        l3 = tf.maximum(alpha * l3, l3)

        # 4. layer4 - [batch size, 14, 14, 128] ==> [batch size, 28, 28, 1]
        l4 = tf.layers.conv2d_transpose(l3, filters=1, kernel_size=n_kernel, strides=2, padding='same',
                                        kernel_initializer=w_init)
        out = tf.tanh(l4)
        return out


def discriminator(x, y=None, reuse=False, is_training=True):
    with tf.variable_scope('discriminator', reuse=reuse):
        alpha = 0.2
        n_filter = 64
        n_kernel = 4
        w_init = tf.contrib.layers.xavier_initializer()

        # 0. concatenate inputs
        # x: [batch size, 28, 28, 1], y: [batch size, 10]
        # make y as same dimension as x first
        if y is not None:
            y_tiled = tf.expand_dims(y, axis=1)
            y_tiled = tf.expand_dims(y_tiled, axis=1)
            y_tiled = tf.tile(y_tiled, multiples=[1, 28, 28, 1])
            inputs = tf.concat([x, y_tiled], axis=3)
        else:
            inputs = x

        # 1. layer 1 - [batch size, 28, 28, 1] ==> [batch size, 14, 14, 64]
        l1 = tf.layers.conv2d(inputs, filters=n_filter, kernel_size=n_kernel, strides=2, padding='same',
                              kernel_initializer=w_init)
        l1 = tf.maximum(alpha * l1, l1)

        # 2. layer 2 - [batch size, 14, 14, 64] ==> [batch size, 7, 7, 128]
        l2 = tf.layers.conv2d(l1, filters=n_filter * 2, kernel_size=n_kernel, strides=2, padding='same',
                              kernel_initializer=w_init)
        l2 = tf.layers.batch_normalization(l2, training=is_training)
        l2 = tf.maximum(alpha * l2, l2)

        # 3. layer 3 - [batch size, 7, 7, 128] ==> [batch size, 4, 4, 256]
        l3 = tf.layers.conv2d(l2, filters=n_filter * 4, kernel_size=n_kernel, strides=2, padding='same',
                              kernel_initializer=w_init)
        l3 = tf.layers.batch_normalization(l3, training=is_training)
        l3 = tf.maximum(alpha * l3, l3)

        # 4. flatten layer & fully connected layer
        # l4 = tf.reshape(l3, shape=[-1, 4 * 4 * 256])
        l4 = tf.contrib.layers.flatten(l3)

        # final logits
        logits = tf.layers.dense(l4, units=1, kernel_initializer=w_init)

        return logits, l4


def classifier(x, out_dim, reuse=False, is_training=True):
    with tf.variable_scope("classifier", reuse=reuse):
        alpha = 0.2

        # 1. layer 1 - fully connected layer
        l1 = tf.layers.dense(x, 128)
        l1 = tf.layers.batch_normalization(l1, training=is_training)
        l1 = tf.maximum(alpha * l1, l1)

        # final logits
        logits = tf.layers.dense(l1, out_dim)

        return logits
