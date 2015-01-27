# -*- coding: utf-8 -*-

from app_tt.pb_apps.pb_task import pb_task
from app_tt.core import pbclient, logger
import ttapps
from app_tt.core import app
from subprocess import call
import requests
from requests import RequestException
import json
import sys
import os
import cells_util
import math
from operator import itemgetter
from app_tt.data_mngr import data_manager
from app_tt.pb_apps.tt_apps import priority_task_manager

from app_tt.meb_exceptions.meb_exception import Meb_exception_tt1, \
    Meb_exception_tt2, Meb_exception_tt3, Meb_exception_tt4, Meb_exception
from app_tt.meb_exceptions.meb_file_output_exception import Meb_file_output_exception_tt2,\
    Meb_file_output_exception_tt3

"""
    Table transcriber tasks
    ~~~~~~~~~~~~~~~~~~~~~~
"""

class TTTask1(pb_task):
    """
    Table Transcriber Task type 1
    
    """
    
    def __init__(self, task_id, app_short_name):
        super(TTTask1, self).__init__(task_id, app_short_name)

    def add_next_task(self):
        try:
            # Verify the answer of the question to create a new task
            if (self.task.info.has_key("answer") and self.task.info["answer"] == "Yes"):
                
                # record a page on mbdb
                bookId = self.get_book_id()
                archurl = self.task.info["url_m"]
                pg = self.task.info["page"]
                data_manager.record_page(dict(bookid=bookId, archiveURL=archurl, page_num=pg))
        
                if (self.__checkIfNextTaskWasCreated()):
                    logger.warn(Meb_exception_tt1(3, self.task.id))
                    raise Meb_exception_tt1(3, self.task.id)    
                
                info = dict(link=self.task.info["url_m"],
                            page=self.task.info["page"])
                tt2_app_short_name = self.app_short_name[:-1] + "2"
                tt2_app = ttapps.Apptt_meta(short_name=tt2_app_short_name)
                
                tt2_task = tt2_app.add_task(info)
                
                workflow_transaction_info = dict(task_id_1=self.task.id, task_id_2=tt2_task.id, task_id_3=None, task_id_4=None)
                data_manager.update_workflow_transaction_t2(workflow_transaction_info)
                
                return True
            else:
                raise Meb_exception_tt1(1, self.task.id)
        except Meb_exception_tt1 as e:
            logger.error(e)
            return False

    def special_close_task(self):
        self.task.state = "completed"
        self.task.info["answer"] = "Yes"
        pbclient.update_task(self.task)

    def check_answer(self):
        try:
            task_runs = self.get_task_runs()
            N_ANSWERS = 2
            answers = {}
            for taskrun in task_runs:
                answer = taskrun.info
                if(answer not in answers.keys()):
                    answers[answer] = 1
                else:
                    answers[answer] += 1
    
                if(answers[answer] == N_ANSWERS and answer != "NotKnown"):
                    self.task.info["answer"] = answer
                    
                    # put the answer into task info
                    pbclient.update_task(self.task)                
                    return True
        
        except Exception:
            logger.error(Meb_exception_tt1(2, self.task.id))
            raise Meb_exception_tt1(2, self.task.id)

    def get_next_app(self):
        curr_app_name = self.app_short_name
        next_app_name = curr_app_name[:-1] + "2"
        return ttapps.Apptt_meta(short_name=next_app_name)

    def __checkIfNextTaskWasCreated(self):
        page_num = self.task.info['page']
        tt2_app = self.get_next_app()
        tt2_tasks = tt2_app.get_tasks()

        for t in tt2_tasks:
            if (t.info['page'] == page_num):
                return True
        return False

class TTTask2(pb_task):
    """
    Table Transcriber Task type 2
    """
    def __init__(self, task_id, app_short_name):
        super(TTTask2, self).__init__(task_id, app_short_name)

    def add_next_task(self):

        # Get the list of task_runs
        task_runs = self.get_task_runs()
        task_run = task_runs[-1]  # Get only the last answer
        
        answer = task_run.info
        answer_info_json = json.loads(answer)
        
        if (answer != "0"): # page don't have table
            
            # record the page tables and its metadata on mbdb
            self.__record_page_table_and_metadata(answer_info_json)

            if (self.__checkIfNextTaskWasCreated()):
                logger.warn(Meb_exception_tt2(6, self.task.id))
                raise Meb_exception_tt2(6, self.task.id)
            
            tt3_app_short_name = self.app_short_name[:-1] + "3"
            tt3_app = ttapps.Apptt_struct(short_name=tt3_app_short_name)

            bookId = self.get_book_id()
            imgId = self.task.info["page"]
            rotate = answer_info_json[0]["text"]["girar"]
                        
            try:
                self.__downloadArchiveImages(bookId, imgId)
                self.__runLinesRecognition(bookId, imgId, rotate)
    
                # file with the lines recognized
                arch = open(
                    "%s/books/%s/metadados/saida/image%s_model%s.txt" % (
                    app.config['CV_MODULES'], bookId, imgId, "1"))
                
                # get the lines recognitions
                tables_coords = self.__splitFile(arch)
                t3_tasks = []
                
                for tableId in range(len(tables_coords)):
                    self.__runAreaSelection(bookId, imgId, tableId, rotate)

                    image_pieces = self.__getAreaSelection(bookId, imgId, tableId)
                    
                    table_subject_code = answer_info_json[tableId]['text']['assunto']

                    next_task_priority = priority_task_manager.get_priority(table_subject_code)
                    
                    if (len(image_pieces) > 0):
                        for image_piece in image_pieces:
                            info = dict(hasZoom=True, zoom=image_piece,
                                        coords=tables_coords[tableId],
                                        table_id=tableId,
                                        page=imgId, img_url=self.__url_table(
                                        bookId, imgId, tableId))
                            t3_tasks.append(tt3_app.add_task(info, priority=next_task_priority))  # add task to tt3_backend
                            
                    else:
                        info = dict(hasZoom=False,
                                    coords=tables_coords[tableId],
                                    table_id=tableId,
                                    page=imgId, img_url=self.__url_table(
                                    bookId, imgId, tableId))
                        t3_tasks.append(tt3_app.add_task(info, priority=next_task_priority))
                    
                    workflow_transaction = data_manager.get_workflow_transaction_by_task_id_2(self.task.id)
                    workflow_transaction_info = dict(task_id_1=workflow_transaction.task_id_1, task_id_2=workflow_transaction.task_id_2, task_id_3=workflow_transaction.task_id_3, task_id_4=workflow_transaction.task_id_4)
                    
                    for i in range(0, len(t3_tasks)):
                        workflow_transaction_info['task_id_3'] = t3_tasks[i].id
                        if i == 0:
                            data_manager.update_workflow_transaction_t3(workflow_transaction_info)
                        else:
                            data_manager.record_workflow_transaction(workflow_transaction_info)
                        
                return True
                
            except Meb_exception_tt2 as e:
                raise e
            
        return False

    def __record_page_table_and_metadata(self, answers):
        # retrieve page (testar none)
        book_id = self.get_book_id()
        page_num = self.task.info["page"]
        page = data_manager.get_page(book_id, page_num)
        
        if (page == None):
            logger.warn("The page from the book " + book_id + " and page number " +  str(page_num) + " doesn't exist.")
            return
        
        for i in range(0, len(answers)):
            answer = answers[i]
            page_table_dict = dict(bookid=book_id, pageid=page.id, local_url="/books/" + book_id + "/metadados/tabelasBaixa/image" + str(page_num) + "_" + str(i) + ".png", top_pos=answer['top'], left_pos=answer['left'], right_pos=(answer['left'] + answer['width']), bottom_pos=(answer['top'] + answer['height']))
            data_manager.record_page_table(page_table_dict)
            
            # retrieve page table
            page_table = data_manager.get_page_table_by_position(page.id, page_table_dict['top_pos'], page_table_dict['left_pos'], page_table_dict['right_pos'], page_table_dict['bottom_pos'])
            
            if (page_table == None):
                logger.warn("The page table from the book " + book_id + " and page " +  str(page.id) + " doesn't exist.")
                return
            
            metadata = answer['text']
            subject_name = priority_task_manager.get_subject(metadata['assunto'])
            
            data_manager.record_metadata(dict(bookid=book_id, pageid=page.id, pagetableid=page_table.id, source=metadata['fontes'], title=metadata['titulo'], subtitle=metadata['subtitulo'], subject=(metadata['outros'] if subject_name == "Outros" else subject_name), initial_date=metadata['dataInicial'], final_date=metadata['dataFinal']))


    def __checkIfNextTaskWasCreated(self):
        page_num = self.task.info['page']
        tt3_app = self.get_next_app()
        tt3_tasks = tt3_app.get_tasks()

        for t in tt3_tasks:
            if (t.info['page'] == page_num):
                return True
        return False

    def check_answer(self):
        task_runs = self.get_task_runs()
        n_taskruns = len(task_runs)  # task_runs goes from 0 to n-1
        
        try:
            if(n_taskruns > 1):
                answer1 = task_runs[n_taskruns - 1].info
                answer2 = task_runs[n_taskruns - 2].info
                answer1_json = json.loads(answer1)
                answer2_json = json.loads(answer2)
                
                if self.__compare_answers(answer1_json, answer2_json):
                    if answer2 != "0":
                        return self.__fileOutput(answer2_json)
                
                return False
        
        except Exception as ex:
            logger.error(Meb_exception_tt2(1, self.task.id))
            logger.error(ex)
            raise Meb_exception_tt2(1, self.task.id)

    def __compare_answers(self, answer1, answer2):
        THRESHOLD = 2
        
        try:
            # TODO: RESOLVER ISSO DEPOIS: CASO EM QUE USUARIO NAO FAZ MARCACAO NA PAGINA
            if answer1 == 0 or answer2 == 0:
                return False
            
            if len(answer1) != len(answer2):
                return False
            
            for i in range(0, min(len(answer2), len(answer1))):
                table1 = answer1[i]
                table2 = answer2[i]
        
                for answer_key in table1.keys():
                    a1_value = table1[answer_key]
                    a2_value = table2[answer_key]
                    if answer_key in ["top", "left", "width", "height"]:
                        if a2_value < (a1_value - THRESHOLD) or a2_value > (a1_value + THRESHOLD):
                            return False
                    elif answer_key in ["text"]:
                        if a1_value["assunto"] != a2_value["assunto"]:
                            return False
                    else: # some other key differ
                        if a1_value != a2_value:
                            return False
                        
            return True
        
        except Exception as ex:
            logger.error(Meb_exception_tt2(1, self.task.id))
            logger.error(ex)
            raise Meb_exception_tt2(1, self.task.id)

    def get_next_app(self):
        curr_app_name = self.app_short_name
        next_app_name = curr_app_name[:-1] + "3"
        return ttapps.Apptt_struct(short_name=next_app_name)

    def __downloadArchiveImages(self, bookId, imgId, width=550, height=700, max_width=1650, max_height=2100):
        """
        Download internet archive images to tt3_backend project
        
        :returns: True if the download was successful
        :rtype: bool
        
        """

        try:
            archiveURL = "http://archive.org/download/%s/page/n%s_w%s_h%s" % (
                bookId, imgId, max_width, max_height)
            
            logger.info("Downloading archive image: " + archiveURL)
            
            url_request = requests.get(archiveURL)

            fullImgPath = "%s/books/%s/alta_resolucao/image%s" % (
                app.config['CV_MODULES'], bookId, imgId)
            fullImgPathJPG = fullImgPath + ".jpg"
            fullImgPathPNG = fullImgPath + ".png"

            fullImgFile = open(fullImgPathJPG, "w")
            fullImgFile.write(url_request.content)
            fullImgFile.close()
    
            # shell command to convert jpg to png
            command = 'convert %s -resize %dx%d! %s; rm %s; ' % (
                fullImgPathJPG, max_width, max_height, fullImgPathPNG, fullImgPathJPG)

            # create image with low resolution
            lowImgPath = "%s/books/%s/baixa_resolucao/image%s" % (
                app.config['CV_MODULES'], bookId, imgId)
            lowImgPathPNG = lowImgPath + ".png"

            command += 'convert %s -resize %dx%d! %s' % (
                fullImgPathPNG, width, height, lowImgPathPNG)
            
            msg = "Command to download archive images: " + command
            logger.info(msg)
            
            call([command], shell=True)  # calls the shell command
            
            return True
        
        except Exception as ex:
            logger.error(Meb_exception_tt2(5, self.task.id))
            logger.error(ex)
            raise Meb_exception_tt2(5, self.task.id)

        return False

    def __runLinesRecognition(self, bookId, imgId, rotate, model="1"):
        """
        Call cpp software that recognizes lines into the table and
        writes lines coords into \
        <tt3_backend_dir>/books/bookId/metadados/saida/image<imgId>.txt

        :returns: True if the write was successful
        :rtype: bool
        
        """
        
        try:
            if rotate:  # rotated table
                rotate = "-r"
                command = 'cd %s/TableTranscriber2/; sudo ./tabletranscriber2 ' \
                '"/books/%s/baixa_resolucao/image%s.png" "model%s" "%s"' % (
                app.config['CV_MODULES'], bookId, imgId, model, rotate)
                
                msg = "Command to run lines recognition software: " + command
                logger.info(msg)
                
                call([command], shell=True)  # calls the shell command
            
            else:  # not rotated table
                rotate = "-nr"
                command = 'cd %s/TableTranscriber2/; sudo ./tabletranscriber2 ' \
                '"/books/%s/baixa_resolucao/image%s.png" "model%s" "%s"' % (
                app.config['CV_MODULES'], bookId, imgId, model, rotate)
                
                msg = "Command to run lines recognition software: " + command
                logger.info(msg)
                
                call([command], shell=True)  # calls the shell command
                
            return self.__checkFile(bookId, imgId)
            
        except Meb_exception_tt2 as e:
            logger.error(Meb_exception_tt2(3, self.task.id))
            raise e
        except Exception as ex:
            logger.error(Meb_exception_tt2(2), self.task.id)
            raise ex
            
    def __checkFile(self, bookId, imgId):
        directory = "%s/books/%s/metadados/saida/" % (
            app.config['CV_MODULES'], bookId)
        output_files = os.listdir(directory)
        images = [f.split('_')[0] for f in output_files]
        
        ans = ("image%s" % imgId) in images
    
        if ans:
            return True
        else:
            raise Meb_exception_tt2(3, self.task.id)
            
    def __runAreaSelection(self, bookId, imgId, tableId, rotate):
        """
        Call cpp ZoomingSelector software that splits the
        tables and write the pieces at
        <tt3_backend_id>/books/bookId/selections/image<imgId>_tableId.txt

        :returns: True if the execution was ok
        :rtype: bool
        """
        try:
            command = 'cd %s/ZoomingSelector/; sudo ./zoomingselector ' \
            '"/books/%s/metadados/tabelasAlta/image%s_%d.png"' % (
            app.config['CV_MODULES'], bookId, imgId, tableId)
            
            msg = "Command to run zoomingselector (area selection software) " + command 
            logger.info(msg)
            
            call([command], shell=True)
        
        except Exception as ex:
            logger.error(Meb_exception_tt2(4, self.task.id))
            raise ex

    def __getAreaSelection(self, bookId, imgId, tableId):

        selections = []

        try:
            filepath = "%s/books/%s/selections/image%s_%d.txt" % (
                app.config['CV_MODULES'], bookId, imgId, tableId)
            arch = open(filepath)
            data = arch.read().strip().split('\n')

            for data_idx in range(1, len(data)):
                selections.append([
                    int(coord) for coord in data[data_idx].split(',')])

        except IOError as ioe:
            msg = "Error! Couldn't open image%s_%d.txt selection file" % (imgId, tableId)
            logger.error(Meb_exception_tt2(4, self.task.id))
            logger.error(msg)
            raise ioe
        except Exception as ex:
            logger.error(Meb_exception_tt2(4, self.task.id))
            raise ex

        return selections

    def __url_table(self, bookId, imgId, idx):
        """""
        Build a url of a splited image for the lines recognizer
        
        :returns: a indexed book table image
        :rtype: str
        
        """
        
        return "%s/books/%s/metadados/tabelasBaixa/image%s_%d.png" % (
            app.config['URL_TEMPLATES'], bookId, imgId, idx)

    def __splitFile(self, arch):
        """""
        Splits a given file and return a matrices list \
        where the lines with '#' are the index and the other \
        lines with values separated with ',' are the vectors \
        of the inner matrices

        :returns: a list of matrix
        :rtype: list
        
        """

        strLines = arch.read().strip().split("\n")
        matrix = []
        matrix_index = -1

        for line in strLines:
            if line.find("#") != -1:
                matrix_index += 1
                matrix.append([])
            else:
                line = line.split(",")
                for char_idx in range(len(line)):
                    line[char_idx] = int(line[char_idx])  # int cast

                matrix[matrix_index].append(line)

        arch.close()
        
        #print "matrix: " + str(matrix)
        
        return matrix

    def __fileOutput(self, answer):
        """""
        Writes tt2 answers into the file input for the lines recognitions

        :returns: True if the answer is saved at the file
        :rtype: bool
        """

        try:
            pb_app_name = self.app_short_name
            bookId = pb_app_name[:-4]
            imgId = self.task.info["page"]
            
            msg = "File path:" + "%s/books/%s/metadados/entrada/image%s.txt" % \
                (app.config["CV_MODULES"], bookId, imgId), "a"
            logger.info(msg)
            
            arch = open("%s/books/%s/metadados/entrada/image%s.txt" % (
                app.config["CV_MODULES"], bookId, imgId), "w")
            for table in answer:
                x0 = int(table["left"])
                x1 = int(table["width"] + x0)
                y0 = int(table["top"])
                y1 = int(table["height"] + y0)
                arch.write(
                    str(x0) + "," + str(y0) + "," + 
                    str(x1) + "," + str(y1) + "\n")
            arch.close()

            return True
        
        except IOError as e:
            print e
            logger.error(Meb_file_output_exception_tt2(1, self.task.id, bookId, imgId))
            raise Meb_file_output_exception_tt2(1, self.task.id, bookId, imgId)

        return False


class TTTask3(pb_task):
    """
    Table Transcriber Task type 3
    """
    def __init__(self, task_id, app_short_name):
        super(TTTask3, self).__init__(task_id, app_short_name)

    def add_next_task(self):

        if (self.__checkIfNextTaskWasCreated()):
            logger.warn(Meb_exception_tt3(3, self.task.id))
            raise Meb_exception_tt3(3, self.task.id)
        
        try:
            linesAndColumnsMap = self.__loadAnswers()
            
            # didnt found a valid task group
            if self.task.info['hasZoom'] and linesAndColumnsMap == None:  
                return False
            
            cells = cells_util.create_cells(linesAndColumnsMap["linhas"], 
                                           linesAndColumnsMap["colunas"], 
                                           linesAndColumnsMap["maxX"],
                                           linesAndColumnsMap["maxY"])
            
            linkImg = self.task.info['img_url']
            book_id = self.get_book_id()
            page = self.task.info['page']
            table_id = self.task.info['table_id']
            maxX = linesAndColumnsMap["maxX"]
            maxY = linesAndColumnsMap["maxY"]
            
            self.__runOCR(cells, book_id, page, table_id, maxX, maxY)
            
            values = self.__loadValues(book_id, page, table_id)
            confidences = self.__loadConfidences(book_id, page, table_id)
            
            infoDict = {}
            infoDict['cells'] = cells
            infoDict['img_url'] = linkImg
            infoDict['page'] = page
            infoDict['table_id'] = table_id
            infoDict['maxX'] = maxX
            infoDict['maxY'] = maxY
            infoDict['values'] = values
            infoDict['confidences'] = confidences
            
            tt4_app_short_name = self.app_short_name[:-1] + "4"
            tt4_app = ttapps.Apptt_transcribe(short_name=tt4_app_short_name)
            tt4_task = tt4_app.add_task(infoDict, priority=self.task.priority_0)
            
            workflow_transaction_info = dict(task_id_1=None, task_id_2=None, task_id_3=self.task.id, task_id_4=tt4_task.id)
            data_manager.update_workflow_transaction_t4(workflow_transaction_info)
            
            return True
        
        except Exception as e:
            logger.error(e)
            raise e
    
    def __checkIfNextTaskWasCreated(self):
        img_url = self.task.info['img_url']
        tt4_app = self.get_next_app()
        tt4_tasks = tt4_app.get_tasks()
        
        for t in tt4_tasks:
            if (t.info['img_url'] == img_url):
                return True

        return False
    
    def __loadAnswers(self):
        """
         Returns the info in json format to tasks, be them either zoom
         or not.
         
         obs.: the properties returned in json_answer are modified in this method: if
         the task has zoom, the answer equivalent to the group of tasks similar to this
         will be returned, in the same format of one simple task, without zoom.
        """
        
        if(self.task.info['hasZoom']):
            
            similarTasks = self.__searchSimilarsTasks()
                
            if(not self.__validateTaskGroup(similarTasks)):
                logger.info("** Invalid task group detected **")
                return
            else:
                groupedAnswers = self.__joinTaskGroupAnswers(similarTasks)
            
                answer_json = {}
                answer_json['linhas'] = groupedAnswers['lines']
                answer_json['colunas'] = groupedAnswers['columns']
                answer_json['maxX'] = groupedAnswers['maxX']
                answer_json['maxY'] = groupedAnswers['maxY']
                
                return answer_json
        else:
            task_runs = self.get_task_runs()
            
            task_run = task_runs[-1]  # Get the last answer
            answer = task_run.info
            answer_json = json.loads(answer)
            
            return answer_json
    
    def __searchSimilarsTasks(self):
        """
          Search similar tasks to this task in pybossa task table
        """
                
        img_url = self.task.info['img_url']
        table_id = self.task.info['table_id']
        
        similarTasks = []
        tasks = self.__get_tasks()
        
        for t in tasks:
            if (t.info['img_url'] == img_url and t.info['table_id'] == table_id):
                similarTasks.append(t)
        
        return similarTasks
    
    def __get_tasks(self):
        """
         Get tasks with self.app_id
        """
        
        return pbclient.get_tasks(self.task.app_id, sys.maxint)
    
    def __validateTaskGroup(self, similarTasks):
        """
          Verify if all tasks, that are similar to this task, and this task
          are completed.
        """
        
        #NUMBER_OF_SIMILAR_TASKS = 3
        
        for t in similarTasks:
            if(not t.state == "completed"):
                m = "invalid task (not completed): " + str(t)
                logger.warn(m)
                return False
        
        #m1 = "similar tasks: " + str(similarTasks)
        #m2 = "self.task.state: " + str(self.task.state)
        #logger.warn(m1)
        #logger.warn(m2)
        
        return True #self.task.state == "completed" and len(similarTasks) == NUMBER_OF_SIMILAR_TASKS
    
    
    def __joinTaskGroupAnswers(self, similarTasks):
        """
          Join all answers of task_runs to return a table grid.
        """
        
        similarTaskRunsAnswers = self.__loadSimilarsTaskRunsAnswers(similarTasks)
        
        lines = []
        columns = []
        maxX = 0
        maxY = 0
              
        for info in similarTaskRunsAnswers:
            for c in info['colunas']:
                columns.append(c)

            for l in info['linhas']:
                overlapping_line = self.__getLineOverlapping(l, lines)

                if (overlapping_line == -1):
                    lines.append(l)
                else:
                    newY = overlapping_line[1]
                    columns = self.__updateColumnsYAxis(l, columns, newY)
            
            if maxX < info['maxX']:
                maxX = info['maxX']
            if maxY < info['maxY']:
                maxY = info['maxY']
        
        mapWithNewAnswer = self.__transformSegmentsInLines(lines, columns)
        mapWithNewAnswer['maxX'] = maxX
        mapWithNewAnswer['maxY'] = maxY
        
        return mapWithNewAnswer
    
    def __loadValues(self, book_id, page, table_id):
        """
         Load values transcripted by tesseract ocr for this table
        """
        
        try:
            f = open("%s/books/%s/transcricoes/texts/image%s_%s.txt" % (
                           app.config['CV_MODULES'], book_id, page, table_id), 'r')
            tmp = f.readlines()
            f.close()
            
            values = []
            for val in tmp[1:]:
                values.append(val[:-1]) # exclude \n
            
            return values #excluding header
        
        except IOError as ioe:
            logger.error(ioe)
            raise Meb_exception_tt3(5, self.task.id)
        
    
    def __loadConfidences(self, book_id, page, table_id):
        """
         Load confidences identified in transcriptions by tesseract ocr for
         this table.
        """
        
        try:
            f = open("%s/books/%s/transcricoes/confidences/image%s_%s.txt" % (
                           app.config['CV_MODULES'], book_id, page, table_id), 'r')
            tmp = f.readlines()
            
            f.close()
            
            confidences = []
            for conf in tmp[1:]:
                confidences.append( int(conf[:-1])) # exclude \n
            
            return confidences # excluding header

        except IOError as ioe:
            logger.error(ioe)
            raise Meb_exception_tt3(6, self.task.id)
    
    
    def __runOCR(self, cells, book_id, page, table_id, maxX, maxY):
        """
          Run tesseract executor
        """
        
        self.__saveCells(cells, book_id, page, table_id, maxX, maxY)
        
        try:
            command = 'cd %s/TesseractExecutorApp2/; sudo ./tesseractexecutorapp2 ' \
            '"/books/%s/metadados/tabelasAlta/image%s_%d.png"' % (
            app.config['CV_MODULES'], book_id, page, table_id)
            
            msg = "Command to run tesseract executor: " + command
            logger.info(msg)
            
            call([command], shell=True)

        except Exception as ex:
            logger.error(Meb_exception_tt3(4, self.task.id))
            raise ex
        

    def __saveCells(self, cells, book_id, page, table_id, maxX, maxY):
        """
          Save cells in /books/<book_id>/metadados/respostaUsuarioTT/image<page>_<table_id>.png
          
          obs.: the algorithm used open the file two times for
           doesn't accept duplicated answers.
        """
        
        try:
            # file with the cells identified by users
            
            header = "#0,0" + "," + str(maxX) + "," + str(maxY) + "\n"
            arch = open("%s/books/%s/metadados/respostaUsuarioTT/image%s_%s.txt" % (
                       app.config['CV_MODULES'], book_id, page, table_id), 'w')
            arch.write(header)
            arch.close()
            
            arch = open("%s/books/%s/metadados/respostaUsuarioTT/image%s_%s.txt" % (
                       app.config['CV_MODULES'], book_id, page, table_id), 'a')
            for cell in cells:
                cStr = str(cell[0]) + "," + str(cell[1]) + "," + str(cell[2]) + "," + str(cell[3]) + "\n"
                arch.write(cStr)
            
            arch.close()
        
        except IOError as ioe:
            raise Meb_file_output_exception_tt3(1, self.task.id, self.task.get_book_id(),
                                                       page, table_id)
        except Exception as e:
            raise e
    
    def __loadSimilarsTaskRunsAnswers(self, similarTasks):
        """
         Load last answer in json format of the last task_run of
         each task in similarTasks.
        """
        
        tasksRunsAnswers = []
        for t in similarTasks: 
            task_runs = json.loads(requests.get(
                    "%s/api/taskrun?task_id=%s&limit=%d" % (
                        app.config['PYBOSSA_URL'], t.id, sys.maxint)).content)
                
            task_run = task_runs[len(task_runs) - 1]  # Get the last answer
            answer = task_run["info"]
            answer_json = json.loads(answer)
            tasksRunsAnswers.append(answer_json)
        
        return tasksRunsAnswers
    
    def __getLineOverlapping(self, line, lines):
        MIN_GAP_BETWEEN_LINES = 5
        for i in range(0, len(lines)):
            other_line =  lines[i]
            
            if ((line[0] == other_line[0] or self.__insideOpenInterval(line[0], line[2], other_line[0]) or self.__insideOpenInterval(line[0], line[2], other_line[2])) and math.fabs((line[1] - other_line[1])) <= MIN_GAP_BETWEEN_LINES):
                return other_line
  
        return -1

    def __insideOpenInterval(self, init, final, element):
        return element > init and element < final

    """
      Transform segments in horizontal or vertical orientations
      in complete lines.
      
      lines: set of lines of all tasks similars to this
      columns: set of columns of all tasks similars to this
    """
    def __transformSegmentsInLines(self, lines, columns):
        
        mapGroupsOfColumns = {}
        for c1 in columns:
            idGroup = self.__identifyGroupIdInX(mapGroupsOfColumns, c1)
            
            if not mapGroupsOfColumns.has_key(idGroup):
                mapGroupsOfColumns[idGroup] = [c1]
            else:
                mapGroupsOfColumns[idGroup].append(c1)
        
        mapWithLinesAndColumns = self.__joinColumnsInGroup(mapGroupsOfColumns, lines)
        
        #print "mapWithLinesAndColumns"
        #print mapWithLinesAndColumns
        
        return mapWithLinesAndColumns
    
    def __identifyGroupIdInX(self, mapGroupsOfColumns, column):
        MIN_GAP_BETWEEN_COLUMNS_IN_X_AXIS = 10
        
        sortListOfGroupIds = []
        for identifier in mapGroupsOfColumns.keys():
            sortListOfGroupIds.append(float(identifier)) 
        
        sortListOfGroupIds.sort()
        
        for group in sortListOfGroupIds:
            if (math.fabs(column[0] - group) <= MIN_GAP_BETWEEN_COLUMNS_IN_X_AXIS):
                return str(group)
        
        return str(float(column[0]))
        
    """
     Join the columns in the same group to make
     a one or more columns consistents.
    """
    def __joinColumnsInGroup(self, mapGroupsOfColumns, lines):
        finalListOfColumns = []
        
        #print "mapGroupsOfColumns"
        #print mapGroupsOfColumns
        
        for groupOfColumns in mapGroupsOfColumns.values():
            transformationResult = self.__transformGroupInList(groupOfColumns, lines)
            lines = transformationResult['lines']
            columns = transformationResult['columns']
            
            for c in columns:
                finalListOfColumns.append(c)
                       
        #print "finalListOfColumns"
        #print finalListOfColumns

        joinResult = {}
        joinResult['lines'] = lines
        joinResult['columns'] = finalListOfColumns
        
        return joinResult
    
    """
     Transform group of columns in one list of consistent
     columns.
    """
    def __transformGroupInList(self, groupOfColumns, lines):
        MIN_GAP_BETWEEN_COLUMNS_IN_Y_AXIS = 5
        sortedGroupOfColumns = sorted(groupOfColumns, key=itemgetter(1))
        #print "sortedGroupOfColumns"
        #print sortedGroupOfColumns
        
        listOfColumns = []
        
        ptr1 = None
        ptr2 = None
        tmpCols = []

        for i in range(0, len(sortedGroupOfColumns)-1):   # find other columns to join
            ptr1 = sortedGroupOfColumns[i]
            ptr2 = sortedGroupOfColumns[i+1]

            if (ptr2[1] - ptr1[3] <= MIN_GAP_BETWEEN_COLUMNS_IN_Y_AXIS): # is a continuous column
                tmpCols.append(ptr1)
                if(i+1 == len(sortedGroupOfColumns)-1):
                    tmpCols.append(ptr2)
            else:
                if (len(tmpCols) == 0):
                    tmpCols.append(ptr1)

                newX = tmpCols[0][0]
                listOfColumns.append([newX, tmpCols[0][1],
                                      newX, tmpCols[-1][3]])
                lines = self.__updateLinesXAxis(tmpCols, lines, newX)

                tmpCols = [ptr2]
                #print "listOfColumns"
                #print listOfColumns
       
        if (len(sortedGroupOfColumns) == 1):
            tmpCols.append(sortedGroupOfColumns[0])

        newX = tmpCols[0][0]
        listOfColumns.append([newX, tmpCols[0][1],
                              newX, tmpCols[-1][3]])
        lines = self.__updateLinesXAxis(tmpCols, lines, newX)
     
        #print "listOfColumns"
        #print listOfColumns

        transformationResult = {}
        transformationResult['lines'] = lines
        transformationResult['columns'] = listOfColumns
        
        return transformationResult
    
    def __updateLinesXAxis(self, columns, lines, newX):
        for column in columns:
            for i in range(0, len(lines)):
                line = lines[i]
                if line[0] == column[0]:
                    lines[i] = [newX, line[1], line[2], line[3]]
                elif line[2] == column[0]:
                    lines[i] = [line[0], line[1], newX, line[3]]
        return lines

    def __updateColumnsYAxis(self, line, columns, newY):
        for i in range(0, len(columns)):
            column = columns[i]
            if column[1] == line[1]:
                columns[i] = [column[0], newY, column[2], column[3]]
            elif column[3] == line[1]:
                columns[i] = [column[0], column[1], column[2], newY]
        return columns

    def check_answer(self):
        task_runs = self.get_task_runs()
        n_taskruns = len(task_runs)  # task_runs goes from 0 to n-1
        
        try:
            if(n_taskruns > 1):
                answer1 = task_runs[n_taskruns - 1].info
                answer2 = task_runs[n_taskruns - 2].info
                
                answer1_json = json.loads(answer1)
                answer2_json = json.loads(answer2)
                if(self.__compare_answers(answer1_json, answer2_json)):
                    return True
                else:
                    return False
            else:
                return False
        
        except Meb_exception_tt3 as ex:
            logger.error(ex)
            raise ex

    def __compare_answers(self, answer1, answer2):
        if len(answer1) != len(answer2):
            raise Meb_exception_tt3(2, self.task.id)
        
        col1 = answer1['colunas']
        lin1 = answer1['linhas']
        
        col2 = answer2['colunas']
        lin2 = answer2['linhas']
        
        if (len(col1) != len(col2) or len(lin1) != len(lin2)):
            return False
        else:
            r1 = self.__compareCols(col1, col2) 
            r2 = self.__compareLin(lin1, lin2)
            
            if (r1 and r2):
                return True
            else:
                return False
    
    def __compareCols(self, column1, column2):
        """
         Compare columns of different answers. Return true if <column1> and
         <column2> are the same.
        """
        
        THRESHOLD = 5
        
        for i in range(0,len(column1)):
            for j in range(0, 4):
                if (column1[i][j] > (column2[i][j] + THRESHOLD) or column1[i][j] < (column2[i][j] - THRESHOLD)):
                    return False
                    
        return True
    
    def __compareLin(self, line1, line2):
        """
         Compare lines of different answers. Return true if <line1> and
         <line2> are the same.
        """
        
        THRESHOLD = 5
        
        for i in range(0, len(line1)):
            for j in range(0, 4):
                if (line1[i][j] > (line2[i][j] + THRESHOLD) or line1[i][j] < (line2[i][j] - THRESHOLD)):
                    return False
        
        return True
    
    def get_next_app(self):
        curr_app_name = self.app_short_name
        next_app_name = curr_app_name[:-1] + "4"
        return ttapps.Apptt_transcribe(short_name=next_app_name)
    
class TTTask4(pb_task):
    """
    Table Transcriber Task type 4
    """
    
    def __init__(self, task_id, app_short_name):
        super(TTTask4, self).__init__(task_id, app_short_name)
        
    def add_next_task(self):
        # Get the list of task_runs
        task_runs = self.get_task_runs()
        task_run = task_runs[-1]  # Get only the last answer
        
        answer = task_run.info
        answer_info_json = json.loads(answer)
        
        self.__record_cells(answer_info_json)
        
        #TODO
        return
    
    def __record_cells(self, answer_json):
        book_id = self.get_book_id()
        page_num = self.task.info["page"]
        page = data_manager.get_page(book_id, page_num)
        
        if (page == None):
            logger.warn("The page from the book " + book_id + " and page number " +  str(page_num) + " doesn't exist.")
            return
        
        cells = answer_json['cells']
        human_values = answer_json['human_values']
        
        for i in range(0, len(cells)):
            cell = cells[i]
            human_value = human_values[i]
            
            # retrieve page table
            page_table = data_manager.get_page_table_by_local_url(page.id, self.task.info["img_url"])
            
            if (page_table == None):
                logger.warn("The page table from the book " + book_id + " and page " +  str(page.id) + " doesn't exist.")
                return
            
            cell_info_dict = dict(bookid=book_id, pageid=page.id, pagetableid=page_table.id, text=human_value, x0=cell[0], y0=cell[1], x1=cell[2], y1=cell[3])
            data_manager.record_cell(cell_info_dict)
    
    def check_answer(self):
        task_runs = self.get_task_runs()
        n_taskruns = len(task_runs)  # task_runs goes from 0 to n-1
        
        try:
            if (n_taskruns > 0):
                last_answer_info = task_runs[-1].info
                last_answer_info_json = json.loads(last_answer_info)
                confirmations = last_answer_info_json['num_of_confirmations']
    
                for confirmation in confirmations:
                    if (int(confirmation) < 2):
                        return False
                return True
            else:
                return False
        
        except Exception as e:
            logger.error(Meb_exception_tt4(1, self.task.id))
            logger.error(e)
            raise Meb_exception_tt4(1, self.task.id)

    def get_next_app(self):
        return
    
    