# -*- coding: utf-8 -*-  
import tensorflow as tf  
import input_dataset  
import forward_prop  
import train  
import math  
import numpy as np  
   
def eval_once(summary_op, summary_writer, saver, predict_true_or_false):  
    with tf.Session() as sess:  
#��checkpoint�ļ��з���checkpointstateģ��  
        checkpoint_proto = tf.train.get_checkpoint_state(checkpoint_dir=train.checkpoint_path)  
        if checkpoint_proto and checkpoint_proto.model_checkpoint_path:  
            saver.restore(sess, checkpoint_proto.model_checkpoint_path)#�ָ�ģ�ͱ�������ǰsession��  
        else:  
            print('checkpoint file not found!')  
            return  
        # �����ܶ��̣߳�����coordinator���ݸ�ÿһ���߳�      
        coord = tf.train.Coordinator() #����һ��coordinator����������ʵ����һ���򵥵Ļ��ƣ���������coordinate�ܶ��̵߳Ľ���  
        try:  
            threads = [] #ʹ��coordͳһ���������߳�  
            for queue_runner in tf.get_collection(key=tf.GraphKeys.QUEUE_RUNNERS):  
                threads.extend(queue_runner.create_threads(sess, coord=coord, daemon=True, start=True))  
#����������ݿ�ĸ���,������ȡ��  
            test_batch_num = math.ceil(input_dataset.test_samples_per_epoch/input_dataset.batch_size)  
            iter_num = 0  
            true_test_num = 0  
#����ʹ��ȡ����Ĳ������ݿ�������������������������Ŀ���������������������������ƫ�󰡣���ʱ��δ��⣿����  
            total_test_num = test_batch_num*input_dataset.batch_size  
              
            while iter_num<test_batch_num and not coord.should_stop():  
                result_judge = sess.run([predict_true_or_false])  
                true_test_num += np.sum(result_judge)  
                iter_num += 1  
            precision = true_test_num/total_test_num  
            print("The test precision is %.3f"  % precision)  
        except:  
            coord.request_stop()  
        coord.request_stop()  
        coord.join(threads)  
                  
def evaluate():  
    with tf.Graph().as_default() as g:  
        img_batch, labels = input_dataset.input_data(eval_flag=True)#����������ݼ�  
        logits = forward_prop.network(img_batch)#ʹ��moving average����ǰ��ģ�Ͳ���������ģ�����ֵ  
#�ж�targets�Ƿ���ǰk��predictions���棬��k=1ʱ�ȼ��ڳ���ļ�����ȷ�ʵķ�����sess.run(predict_true_or_false)��ִ�з��ż���  
        predict_true_or_false = tf.nn.in_top_k(predictions=logits, targets=labels, k=1)  
        #�ָ�moving average�������ģ�Ͳ���  
        moving_average_op = tf.train.ExponentialMovingAverage(decay=forward_prop.moving_average_decay)  
#����Ҫ�ָ���names��Variables��ӳ�䣬Ҳ��һ��mapӳ�䡣���һ��������moving average,��ʹ��moving average��������Ϊthe restore  
# name, �����ʹ�ñ�����  
        variables_to_restore = moving_average_op.variables_to_restore()  
        saver = tf.train.Saver(var_list=variables_to_restore)  
          
        summary_op = tf.merge_all_summaries() #�������л����summary����  
#����һ��event file,����֮��дsummary����logdirĿ¼�µ��ļ���  
        summary_writer = tf.train.SummaryWriter(logdir='./event-log-test', graph=g)  
        eval_once(summary_op, summary_writer, saver, predict_true_or_false)  