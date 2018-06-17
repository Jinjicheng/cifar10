# -*- coding: utf-8 -*-  
import input_dataset  
import forward_prop  
import tensorflow as tf  
import os  
import numpy as np  
   
max_iter_num = 100000 #���ò�����������  
checkpoint_path = './checkpoint' #����ģ�Ͳ����ļ�����·��  
event_log_path = './event-log' #�����¼��ļ�����·�������������Դ洢Summary�������  
   
def train():  
    with tf.Graph().as_default():    #ָ����ǰͼΪĬ��graph  
        global_step = tf.Variable(initial_value=0, trainable=False)#����trainable=False,����Ϊ��ֹѵ�������ж�global_step����Ҳ���л������²���  
        img_batch, label_batch = input_dataset.preprocess_input_data()#����ͼ���Ԥ�����������ȡ��Աȶȡ�ͼ��ת�Ȳ���  
        # img_batch, label_batch = input_dataset.input_data(eval_flag=False)  
        logits = forward_prop.network(img_batch) #ͼ���źŵ�ǰ�򴫲�����  
        total_loss = forward_prop.loss(logits, label_batch) #������ʧ  
        one_step_gradient_update = forward_prop.one_step_train(total_loss, global_step) #����һ���ݶȸ��²���  
        #����һ��saver�������ڱ���������ļ���  
        saver = tf.train.Saver(var_list=tf.all_variables()) #tf.all_variables return a list of `Variable` objects          
        all_summary_obj = tf.merge_all_summaries()#��������summary������merge��serialize��ĵ��ַ�������tensor  
        initiate_variables = tf.initialize_all_variables()          
#log_device_placement�������Լ�¼ÿһ������ʹ�õ��豸������Ĳ����Ƚ϶࣬�Ͳ���Ҫ��¼�ˣ�������ΪFalse  
        with tf.Session(config=tf.ConfigProto(log_device_placement=False)) as sess:  
            sess.run(initiate_variables)  #������ʼ��             
            tf.train.start_queue_runners(sess=sess) #�������е�queuerunners  
            Event_writer = tf.train.SummaryWriter(logdir=event_log_path, graph=sess.graph)   
            for step in range(max_iter_num):  
                _, loss_value = sess.run(fetches=[one_step_gradient_update, total_loss])  
                assert not np.isnan(loss_value) #������֤��ǰ�����������loss_value�Ƿ����  
                if step%10 == 0:  
                    print('step %d, the loss_value is %.2f' % (step, loss_value))  
                if step%100 == 0:  
                    # ���`Summary`Э�黺�浽�¼��ļ��У��ʲ���дtotal_loss�������¼��ļ��У���Ϊ�����total_lossΪ��ͨ��tensor����  
                    all_summaries = sess.run(all_summary_obj)  
                    Event_writer.add_summary(summary=all_summaries, global_step=step)  
                if step%1000 == 0 or (step+1)==max_iter_num:  
                    variables_save_path = os.path.join(checkpoint_path, 'model-parameters.bin') #·���ϲ������غϲ�����ַ���  
                    saver.save(sess, variables_save_path, global_step=step)#�����б���������moving averageǰ���ģ�Ͳ�����������variables_save_path·����                   
if __name__ == '__main__':  
    train()                