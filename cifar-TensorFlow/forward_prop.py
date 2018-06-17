# -*- coding: utf-8 -*-  
import tensorflow as tf  
import input_dataset  
#�ⲿ����input_dataset�ļ��ж����hyperparameters  
height = input_dataset.fixed_height  
width = input_dataset.fixed_width  
train_samples_per_epoch = input_dataset.train_samples_per_epoch  
test_samples_per_epoch = input_dataset.test_samples_per_epoch  
   
# ��������ѵ�����̵ĳ���  
moving_average_decay = 0.9999     # The decay to use for the moving average.  
num_epochs_per_decay = 350.0      # ˥���ʽ��ݺ���������˥�����ڣ����ݿ�ȣ�  
learning_rate_decay_factor = 0.1  # ѧϰ��˥������  
initial_learning_rate = 0.1       # ��ʼѧϰ��  
   
def variable_on_cpu(name, shape, dtype, initializer):  
    with tf.device("/cpu:0"):  #һ�� context manager,����Ϊ�µ�opָ��Ҫʹ�õ�Ӳ��  
        return tf.get_variable(name=name,   
                               shape=shape,   
                               initializer=initializer,  
                               dtype=dtype)      
   
def variable_on_cpu_with_collection(name, shape, dtype, stddev, wd):  
    with tf.device("/cpu:0"):   
        weight = tf.get_variable(name=name,   
                                 shape=shape,   
                                 initializer=tf.truncated_normal_initializer(stddev=stddev, dtype=dtype))  
        if wd is not None:  
            weight_decay = tf.mul(tf.nn.l2_loss(weight), wd, name='weight_loss')  
            tf.add_to_collection(name='losses', value=weight_decay)           
        return weight  
          
def losses_summary(total_loss):  
#ͨ��ʹ��ָ��˥������ά�������Ļ�����ֵ����ѵ��ģ��ʱ��ά��ѵ�������Ļ�����ֵ���кô��ġ��ڲ��Թ�����ʹ�û�������������ѵ���Ĳ���ֵ����  
    #�����ģ�͵�ʵ�����ܣ�׼ȷ�ʣ���apply()���������trained variables��shadow copies������Ӳ�����ά�������Ļ�����ֵ��shadow copies��average  
    #�������Է���shadow variables���ڴ���evaluation modelʱ�ǳ����á�  
#������ֵ��ͨ��ָ��˥������õ��ġ�shadow variable�ĳ�ʼ��ֵ��trained variables��ͬ������¹�ʽΪ  
# shadow_variable = decay * shadow_variable + (1 - decay) * variable  
    average_op = tf.train.ExponentialMovingAverage(decay=0.9) #����һ���µ�ָ��������ֵ����  
    losses = tf.get_collection(key='losses')# ���ֵ伯���з��عؼ���'losses'��Ӧ�����б�����������������ʧ����������ʧ  
    # ������shadow variables��,�����ά��������ֵ�Ĳ���  
    maintain_averages_op = average_op.apply(losses+[total_loss])#ά�������Ļ�����ֵ������һ���ܹ�����shadow variables�Ĳ���  
    for i in losses+[total_loss]:  
        tf.scalar_summary(i.op.name+'_raw', i) #���������Summary��������Ա�д�뵽�ļ���  
        tf.scalar_summary(i.op.name, average_op.average(i)) #average() returns the shadow variable for a given variable.  
    return maintain_averages_op  #������ʧ�����ĸ��²���  
      
def one_step_train(total_loss, step):  
    batch_count = int(train_samples_per_epoch/input_dataset.batch_size) #��ѵ����ĸ���   
    decay_step = batch_count*num_epochs_per_decay #ÿ����decay_step��ѵ����˥��lr  
    lr = tf.train.exponential_decay(learning_rate=initial_learning_rate,  
                                    global_step=step,  
                                    decay_steps=decay_step,  
                                    decay_rate=learning_rate_decay_factor,  
                                    staircase=True)  
    tf.scalar_summary('learning_rate', lr)  
    losses_movingaverage_op = losses_summary(total_loss)  
    #tf.control_dependencies��һ��context manager,���ƽڵ�ִ��˳����ִ��control_inputs�еĲ�������ִ��context�еĲ���  
    with tf.control_dependencies(control_inputs=[losses_movingaverage_op]):  
        trainer = tf.train.GradientDescentOptimizer(learning_rate=lr)  
        gradient_pairs = trainer.compute_gradients(loss=total_loss) #���ؼ�����ģ�gradient, variable�� pairs  
    gradient_update = trainer.apply_gradients(grads_and_vars=gradient_pairs, global_step=step) #����һ���ݶȸ��²���  
    #num_updates�������ڶ�̬����˥���ʣ���ʵ��decay_rate =min(decay, (1 + num_updates) / (10 + num_updates)   
    variables_average_op = tf.train.ExponentialMovingAverage(decay=moving_average_decay, num_updates=step)  
    # tf.trainable_variables() ������������`trainable=True`�ı������б�ṹ  
    maintain_variable_average_op = variables_average_op.apply(var_list=tf.trainable_variables())#����ģ�Ͳ��������Ļ������²���  
    with tf.control_dependencies(control_inputs=[gradient_update, maintain_variable_average_op]):  
        gradient_update_optimizor = tf.no_op() #Does nothing. Only useful as a placeholder for control edges  
    return gradient_update_optimizor                      
      
def network(images):  
#��һ������Ҫ���ü�����������������һƪ���͡�TensorFlowʵ�־�������硯������ϸ���ܣ�����Ͳ���׸����  
    with tf.variable_scope(name_or_scope='conv1') as scope:  
        weight = variable_on_cpu_with_collection(name='weight',   
                                                 shape=(5, 5, 3, 64),   
                                                 dtype=tf.float32,   
                                                 stddev=0.05,  
                                                 wd = 0.0)  
        bias = variable_on_cpu(name='bias', shape=(64), dtype=tf.float32, initializer=tf.constant_initializer(value=0.0))  
        conv1_in = tf.nn.conv2d(input=images, filter=weight, strides=(1, 1, 1, 1), padding='SAME')  
        conv1_in = tf.nn.bias_add(value=conv1_in, bias=bias)  
        conv1_out = tf.nn.relu(conv1_in)   
          
    pool1 = tf.nn.max_pool(value=conv1_out, ksize=(1, 3, 3, 1), strides=(1, 2, 2, 1), padding='SAME')  
      
    norm1 = tf.nn.lrn(input=pool1, depth_radius=4, bias=1.0, alpha=0.001/9.0, beta=0.75)  
      
    with tf.variable_scope(name_or_scope='conv2') as scope:  
        weight = variable_on_cpu_with_collection(name='weight',   
                                 shape=(5, 5, 64, 64),   
                                 dtype=tf.float32,   
                                 stddev=0.05,  
                                 wd=0.0)  
        bias = variable_on_cpu(name='bias', shape=(64), dtype=tf.float32, initializer=tf.constant_initializer(value=0.1))  
        conv2_in = tf.nn.conv2d(norm1, weight, strides=(1, 1, 1, 1), padding='SAME')  
        conv2_in = tf.nn.bias_add(conv2_in, bias)  
        conv2_out = tf.nn.relu(conv2_in)   
      
    norm2 = tf.nn.lrn(input=conv2_out, depth_radius=4, bias=1.0, alpha=0.001/9.0, beta=0.75)  
      
    pool2 = tf.nn.max_pool(value=norm2, ksize=(1, 3, 3, 1), strides=(1, 2, 2, 1), padding='SAME')  
    # input tensor of shape `[batch, in_height, in_width, in_channels]  
    reshaped_pool2 = tf.reshape(tensor=pool2, shape=(-1, 6*6*64))  
      
    with tf.variable_scope(name_or_scope='fully_connected_layer1') as scope:  
        weight = variable_on_cpu_with_collection(name='weight',   
                                                 shape=(6*6*64, 384),   
                                                 dtype=tf.float32,  
                                                 stddev=0.04,  
                                                 wd = 0.004)  
        bias = variable_on_cpu(name='bias', shape=(384), dtype=tf.float32, initializer=tf.constant_initializer(value=0.1))  
        fc1_in = tf.matmul(reshaped_pool2, weight)+bias  
        fc1_out = tf.nn.relu(fc1_in)  
      
    with tf.variable_scope(name_or_scope='fully_connected_layer2') as scope:  
        weight = variable_on_cpu_with_collection(name='weight',   
                                                 shape=(384, 192),   
                                                 dtype=tf.float32,  
                                                 stddev=0.04,  
                                                 wd=0.004)  
        bias = variable_on_cpu(name='bias', shape=(192), dtype=tf.float32, initializer=tf.constant_initializer(value=0.1))  
        fc2_in = tf.matmul(fc1_out, weight)+bias  
        fc2_out = tf.nn.relu(fc2_in)      
      
    with tf.variable_scope(name_or_scope='softmax_layer') as scope:  
        weight = variable_on_cpu_with_collection(name='weight',   
                                                 shape=(192, 10),   
                                                 dtype=tf.float32,  
                                                 stddev=1/192,  
                                                 wd=0.0)  
        bias = variable_on_cpu(name='bias', shape=(10), dtype=tf.float32, initializer=tf.constant_initializer(value=0.0))  
        classifier_in = tf.matmul(fc2_out, weight)+bias  
        classifier_out = tf.nn.softmax(classifier_in)  
    return classifier_out  
   
def loss(logits, labels):   
    labels = tf.cast(x=labels, dtype=tf.int32)  #ǿ������ת����ʹ����sparse_softmax_cross_entropy_with_logits���������ʽҪ��  
    cross_entropy_loss = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=labels, name='likelihood_loss')  
    cross_entropy_loss = tf.reduce_mean(cross_entropy_loss, name='cross_entropy_loss') #��batch_size���ȵ�����ȡƽ��      
    tf.add_to_collection(name='losses', value=cross_entropy_loss) #������cross_entropy_loss��ӵ��ֵ伯����key='losses'���Ӽ���    
    return tf.add_n(inputs=tf.get_collection(key='losses'), name='total_loss') #�����ֵ伯����key='losses'���Ӽ���Ԫ��֮��  