from experta import *
from experta.fact import *
from questions import questions, topics

import sys
import random

class Question(Fact):
    
    question = Field(str)
    answers = Field(str)
    correct_answer = Field(str)

class StudentAnswer(Fact):
    pass

class Action(Fact):
    pass

class ActualQuestion(Fact):
    pass

class CorrectAnswersCounter(Fact):
    count = Field(int)

class QuestionCounter(Fact):
    question_count = Field(int)

class CorrectAnswersInTopic(Fact):
    ans_count = Field(int)

class CurrentTopic(Fact):
    pass

class Topic(Fact):
    topic_number = Field(int)
    questions_list = Field(list)

class Rules(KnowledgeEngine):

    @DefFacts()
    def answers(self):
        '''
        Определение основных фактов
        '''
        for question_number in questions:
            yield Question(question=questions[question_number]['question'], correct_answer=questions[question_number]['correct_answer'])
        for key in topics:
            yield Topic(topic_number=key, questions_list=topics[key]['questions'])

    #Начало работы
    @Rule()
    def start(self):
        print('Начнем задавать вопросы')
        self.declare(QuestionCounter(question_count=0))
        self.declare(CorrectAnswersCounter(count=0))
        self.declare(CorrectAnswersInTopic(ans_count=0))
        
        self.declare(Action('select-topic'))
        
    #Выбор темы
    @Rule(AS.f << Action('select-topic'))
    def select_topic(self, f):
        self.retract(f)
        topic_number = random.choice(list(topics.keys()))
        print('Выбор темы: {}'.format(str(topic_number)))
        self.declare(CurrentTopic(current_topic=topic_number))
        self.declare(Action('select-a-question'))

    #Выбор вопроса
    @Rule(AS.f << Action('select-a-question'),
            AS.tn << CurrentTopic(current_topic=MATCH.t),
            AS.topic << Topic(topic_number = MATCH.t),
            )
    def ask_question(self, f, topic):
        self.retract(f)
        
        question_number = int(random.choice(topic['questions_list']))
        
        
        question = questions[question_number]['question']
        
        answers = questions[question_number]['answers']
        print('---------------------------------------------')
        print(question)
        print(answers)
        
        answer = input()
        
        self.declare(ActualQuestion(question))
        self.declare(StudentAnswer(answer))
        self.declare(Action('check-answer'))

    #Ответ правильный
    @Rule(AS.f1 << Action('check-answer'),
            AS.f2 << ActualQuestion(MATCH.q),
            AS.f3 << StudentAnswer(MATCH.a),
            Question(question = MATCH.q, correct_answer = MATCH.a),
            
            )
    def correct_answer(self, f1, f2, f3):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        print('Ответ верный')
        
        self.declare(Action('increase-correct-answer'))
        
    @Rule(AS.f << Action('increase-correct-answer'),
            AS.c << CorrectAnswersCounter(count = MATCH.counter),
            AS.ct << CorrectAnswersInTopic(ans_count = MATCH.ans_counter),
            AS.qc << QuestionCounter(question_count = MATCH.q))
    def increase_correct_answer(self, c, counter, f, ct, ans_counter, qc, q):
        self.retract(f)
        print('increasing')
        
        self.modify(qc, question_count = q + 1)
        self.modify(ct, ans_count = ans_counter + 1)
        self.modify(c, count = counter + 1)

    #Ответ не правильный
    @Rule(AS.f1 << Action('check-answer'),
            AS.f2 << ActualQuestion(MATCH.q),
            AS.f3 << StudentAnswer(MATCH.a),
            NOT(Question(question = MATCH.q, correct_answer = MATCH.a)),
            AS.qc << QuestionCounter(question_count = MATCH.q_c)
            )
    def incorrect_answer(self, f1, f2, f3, qc, q_c):
        self.retract(f1)
        self.retract(f2)
        self.retract(f3)
        
        print('ответ не верный')
        self.modify(qc, question_count = q_c + 1)
        self.declare(Action('select-a-question'))
    
    
    #Если в текущей теме два правильных ответа, выбор новой темы, иначе сразу же выбор нового вопроса
    @Rule(NOT(CorrectAnswersInTopic(ans_count = L(2))))
    def set_new_question(self):
        print('new question')
        self.declare(Action('select-a-question')) 

    @Rule(AS.f << CurrentTopic(current_topic=MATCH.t),
          AS.f1 << CorrectAnswersInTopic(ans_count = L(2)))
    def set_new_topic(self, f, f1):
        self.retract(f)
        self.modify(f1, ans_count = 0)
        print('new topic')
        self.declare(Action('select-topic'))

    #Подсчет оценки и завершение работы
    @Rule(QuestionCounter(question_count = L(10)),
            AS.ca << CorrectAnswersCounter(count = MATCH.cac),salience = 1)
    def finish_quiz(self, cac):
        mark = int(cac / 2)
        print('Правильных ответов: {}\n Оценка: {}'.format(cac, mark))
        sys.exit()

   

engine = Rules()


engine.reset()
engine.run()
