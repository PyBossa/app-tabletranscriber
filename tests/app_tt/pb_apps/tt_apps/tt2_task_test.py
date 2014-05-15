# -*- coding: utf-8 -*-
from app_tt.pb_apps.tt_apps.tt_tasks import TTTask1
from app_tt.pb_apps.tt_apps.tt_tasks import TTTask2
from app_tt.pb_apps.tt_apps.tt_tasks import TTTask3
from app_tt.pb_apps.tt_apps.tt_tasks import TTTask4
from app_tt.pb_apps.tt_apps.ttapps import Apptt_meta

from app_tt.core import pbclient, app as app_flask
import unittest
import requests
import json
import time

from tests.app_tt.base import delete_book, authenticate_fb_user, submit_answer
from app_tt.data_mngr import data_manager as data_mngr 

from app_tt.meb_exceptions.meb_exception import Meb_pb_task_exception, Meb_exception_tt2

class TT_Task2_TestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = Apptt_meta(short_name="sh_tt2", title="title1")
        self.app.add_task(task_info=dict(link="http://archive.org/download/livro1/n1", page=1))
        self.app.add_task(task_info=dict(link="http://archive.org/download/livro1/n2", page=2))
        
        tasks = pbclient.get_tasks(app_id=self.app.app_id)
        
        self.task1 = TTTask2(tasks[0].id, app_short_name=self.app.short_name)
        self.task2 = TTTask2(tasks[1].id, app_short_name=self.app.short_name)
        
        self.base_url = app_flask.config['PYBOSSA_URL']
        self.fb_user = authenticate_fb_user(self.base_url)
        
        self.book_id = "sh"
        data_mngr.record_book(dict(bookid="sh", title="title1", contributor="cont1", publisher="pub1", volume="1", img="image1"))
        
    def tearDown(self):
        pbclient.delete_task(self.task1.task.id)
        pbclient.delete_task(self.task2.task.id)
        pbclient.delete_app(self.app.app_id)
        
        delete_book(self.book_id)
    
    # testing functions

#     def test_init_01(self):
#         try:
#             t1 = TTTask1( -1, "sh_tt2")
#         except Meb_pb_task_exception as e:
#             self.assertEquals(e.code, 1)
#      
#     def test_init_02(self):
#         try:
#             t1 = TTTask1( self.app.app_id, "sh_t")
#         except Meb_pb_task_exception as e:
#             self.assertEquals(e.code, 2)
#  
#     def test_get_next_app_01(self):
#         try:
#             nx_app = self.task1.get_next_app()
#             self.assertEquals(nx_app.short_name, self.app.short_name[:-1] + "3")
#         except Exception:
#             assert False
#     
    def test_check_answer_01(self):
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
              
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
              
            time.sleep(2)
             
            self.assertTrue(self.task1.check_answer())
              
            trs = self.task1.get_task_runs()
  
            self.assertEquals(trs[0].info, "[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            self.assertEquals(trs[1].info, "[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            
            self.assertTrue(self.task1.check_answer())
            self.assertEquals(self.task1.task.state, '0')
            
            self.task1.close_task()
            
            self.assertEquals(self.task1.task.state, 'completed')
            
        except Exception as e:
            print e
            assert False
      
    def test_check_answer_02(self):
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"2\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
      
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
              
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
              
            time.sleep(2)
              
            self.assertFalse(self.task1.check_answer())
              
        except Exception as e:
            print e
            assert False
     
     
    def test_check_answer_03(self):
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
      
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
              
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
              
            time.sleep(2)
              
            self.task1.check_answer()
              
        except Meb_exception_tt2 as e:
            self.assertEquals(e.code, 1)
     
    def test_check_answer_04(self):
        """
          Detection of some field differing 
        """
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"1900\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
      
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
              
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
              
            time.sleep(2)
              
            self.task1.check_answer()
              
        except Meb_exception_tt2 as e:
            self.assertEquals(e.code, 1)
     
    def test_check_answer_05(self):
        """
          Detection of some field faulting 
        """
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
      
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
              
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
              
            time.sleep(2)
              
            self.task1.check_answer()
              
        except Meb_exception_tt2 as e:
            self.assertEquals(e.code, 1)
    
    def test_add_next_task_01(self):
        """
           Invalid book 'sh' doesn't exists
        """
        
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
     
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
             
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
             
            time.sleep(2)
             
            self.assertTrue(self.task1.check_answer())
            
            self.task1.add_next_task()
             
        except Exception as e:
            assert True
 
    def test_add_next_task_02(self):
        """
           Invalid book
        """
        try:
            task_run1 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":9.5,\"width\":525,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
            task_run2 = dict(app_id=self.app.app_id, task_id=self.task1.task.id, info="[{\"id\":\"new\",\"top\":50,\"left\":15.5,\"width\":625,\"height\":626,\"text\":{\"titulo\":\"\",\"subtitulo\":\"\",\"assunto\":\"4\",\"fontes\":\"\",\"outros\":\"\",\"dataInicial\":\"\",\"dataFinal\":\"\",\"girar\":false,\"nao_girar\":true},\"editable\":true}]")
     
            # Anonymous submission
            submit_answer(self.base_url, task_run1)
             
            # FB authenticated user submission
            task_run2['facebook_user_id'] = '12345'
            submit_answer(self.base_url, task_run2)
             
            time.sleep(2)
             
            self.assertFalse(self.task1.check_answer())
            
            self.task1.add_next_task()
             
        except Meb_exception_tt2 as e:
            self.assertEquals(e.code, 3)

if __name__ == '__main__':
    unittest.main()

