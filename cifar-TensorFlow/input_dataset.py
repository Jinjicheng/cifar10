# -*- coding: utf-8 -*-  
import os  
import tensorflow as tf  
# ԭͼ��ĳ߶�Ϊ32*32,�����ݳ�ʶ����Ϣ����ͨ��λ��ͼ������룬���ﶨ���������Ĳü���ͼ��ĳߴ�  
fixed_height = 24  
fixed_width = 24  
# cifar10���ݼ��ĸ�ʽ��ѵ���������Ͳ����������ֱ�Ϊ50k��10k  
train_samples_per_epoch = 50000  
test_samples_per_epoch = 10000  
data_dir='./cifar-10-batches-bin' # �������ݼ������ļ���·��  
batch_size=128 #����ÿ�β�������ʱ����ʹ�õ�batch�Ĵ�С  
   
def read_cifar10(filename_queue):  
    # ����һ���յ������������c��������Ľṹ�嶨��  
    class Image(object):  
        pass  
    image = Image()  
    image.height=32  
    image.width=32  
    image.depth=3  
    label_bytes = 1  
    image_bytes = image.height*image.width*image.depth  
    Bytes_to_read = label_bytes+image_bytes  
    # ����һ��Reader����ÿ���ܴ��ļ��ж�ȡ�̶��ֽ���  
    reader = tf.FixedLengthRecordReader(record_bytes=Bytes_to_read)   
    # ���ش�filename_queue�ж�ȡ��(key, value)�ԣ�key��value�����ַ������͵�tensor�����ҵ������е�ĳһ���ļ������ʱ�����ļ�����dequeue  
    image.key, value_str = reader.read(filename_queue)   
    # ����������Կ������������ļ������ַ����е��ֽ�ת��Ϊ��ֵ����,ÿһ����ֵռ��һ���ֽ�,��[0, 255]�����ڣ����out_typeҪȡuint8����  
    value = tf.decode_raw(bytes=value_str, out_type=tf.uint8)   
    # ��һάtensor�����н�ȡһ��slice,�����ڴ�һά������ɸѡ����������Ϊvalue�а�����label��feature����Ҫ����������tensor����'parse'����      
    image.label = tf.slice(input_=value, begin=[0], size=[label_bytes])# begin��size�ֱ��ʾ����ȡƬ�ε����ͳ���  
    data_mat = tf.slice(input_=value, begin=[label_bytes], size=[image_bytes])  
    data_mat = tf.reshape(data_mat, (image.depth, image.height, image.width)) #�����ά��˳��������cifar�������ļ��ĸ�ʽ������  
    transposed_value = tf.transpose(data_mat, perm=[1, 2, 0]) #��data_mat��ά�Ƚ����������У�����ֵ�ĵ�i��ά�ȶ�Ӧ��data_mat�ĵ�perm[i]ά  
    image.mat = transposed_value      
    return image      
      
def get_batch_samples(img_obj, min_samples_in_queue, batch_size, shuffle_flag):  
''''' 
tf.train.shuffle_batch()�������������shuffling �����е�tensors������batches(Ҳ��ÿ�ο��Զ�ȡ���data�ļ��е���������һ��batch)�����������ǰGraph����������ж��� 
*������һ��shuffling queue�����ڰѡ�tensors���е�tensorsѹ��ö��У� 
*һ��dequeue_many���������ڸ��ݶ����е����ݴ���һ��batch�� 
*������һ��QueueRunner������������һ������ѹ���ݵ����� 
capacity�������ڿ���shuffling queue����󳤶ȣ�min_after_dequeue������ʾ����һ��dequeue�����������Ԫ�ص���С��������������ȷ��batch�� 
Ԫ�ص�����ԣ�num_threads��������ָ�����ٸ�threads����ѹtensors�����У�enqueue_many�������ڱ����Ƿ�tensors�е�ÿһ��tensor������һ������ 
tf.train.batch()��֮���ƣ�ֻ����˳��س����У�Ҳ��ÿ��ֻ�ܴ�һ��data�ļ��ж�ȡbatch������������ԡ� 
'''  
    if shuffle_flag == False:  
        image_batch, label_batch = tf.train.batch(tensors=img_obj,   
                                                  batch_size=batch_size,   
                                                  num_threads=4,   
                                                  capacity=min_samples_in_queue+3*batch_size)  
    else:  
        image_batch, label_batch = tf.train.shuffle_batch(tensors=img_obj,   
                                                          batch_size=batch_size,   
                                                          num_threads=4,   
                                                          min_after_dequeue=min_samples_in_queue,  
                                                          capacity=min_samples_in_queue+3*batch_size)                                                      
    tf.image_summary('input_image', image_batch, max_images=6) #���Ԥ�����ͼ���summary�������������session��д�뵽�¼��ļ���                                                      
    return image_batch, tf.reshape(label_batch, shape=[batch_size])       
                                         
def preprocess_input_data():  
'''''�ⲿ�ֳ������ڶ�ѵ�����ݼ����С�������ǿ��������ͨ������ѵ�����Ĵ�С����ֹ�����'''  
    filenames = [os.path.join(data_dir, 'data_batch_%d.bin' % i) for i in range(1, 6)]  
    #filenames =[os.path.join(data_dir, 'test_batch.bin')]  
    for f in filenames: #����ѵ�����ݼ��ļ��Ƿ����  
        if not tf.gfile.Exists(f):  
            raise ValueError('fail to find file:'+f)      
    filename_queue = tf.train.string_input_producer(string_tensor=filenames) # ���ļ�������������У���Ϊ����data pipe�ĵ�һ�׶�  
    image = read_cifar10(filename_queue) #���ļ��������ж�ȡһ��tensor���͵�ͼ��  
    new_img = tf.cast(image.mat, tf.float32)  
    tf.image_summary('raw_input_image', tf.reshape(new_img, [1, 32, 32, 3]))#���Ԥ����ǰͼ���summary�������  
    new_img = tf.random_crop(new_img, size=(fixed_height, fixed_width, 3)) #��ԭͼ�����и����ͼ��  
    new_img = tf.image.random_brightness(new_img, max_delta=63) #�������ͼ�������  
    new_img = tf.image.random_flip_left_right(new_img) #��������ҷ�תͼ��  
    new_img = tf.image.random_contrast(new_img, lower=0.2, upper=1.8) #����ص���ͼ��Աȶ�  
    final_img = tf.image.per_image_whitening(new_img) #��ͼ�����whiten������Ŀ���ǽ�������ͼ��������ԣ�����ȥ������������������  
      
    min_samples_ratio_in_queue = 0.4  #����ȷ����ȡ����batch������������ԣ�ʹ�串�ǵ��������𡢸���������ļ�������  
    min_samples_in_queue = int(min_samples_ratio_in_queue*train_samples_per_epoch)   
    return get_batch_samples([final_img, image.label], min_samples_in_queue, batch_size, shuffle_flag=True)