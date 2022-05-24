import simpy
import random
import math

# seed for random library
seed = 2023
# sum of last digits of student ids
S = 453
# decision rule for N which is the population size
if S > 1000:
   N = S
elif S > 10:
  N = S + 1000
else:
  N = S * 300

# decision rule for K which is the available beds in the hospital
K = math.ceil(N/24)

# given mu1 which is associated with the healing time who treated in //hospital
mu1 = 1/6.
# given mu2 which is associated with the healing time who wants to treatment
# in their home
mu2 = 0.1
# mu3 rule which is associated with the healing time who wanted to be //treated
mu3 = mu1 * random.uniform(1, 2)
# probability of choosing home or hospital treatment
p = 0.2

# time intervals for regarding fullness of beds
bed_list = []
# service times of ordered patients
service_times = []
# given time limitations
finish_time = 1000
# arranging previously describe list
for i in range(K+1):
    bed_list.append([])


# Person class who choosen as patient
class Person(object):
    # we asked to give output for first 50 events,
    # this variable counts it
    written = 0
    # number of sick people at the current time
    num_of_sick = 0
    # number of used bed at the current time
    num_of_used_bed = 0
    # last event time
    last_time = 0
    # constructor of a person class
    # encapsulates information anout simpy environment,
    # name, and the choosen healing process
    def __init__(self, name, env, decision):
        self.env = env
        self.name = name
        self.arrival_t = self.env.now
        self.decision = decision
        self.action = env.process(self.sick())

    #  becoming sick
    def sick(self):
        # updating the value of counts of sick people
        Person.num_of_sick += 1
        # bed check operations and choosing random healing time
        # regarding to our constraints
        # we assure the using type of healing and giving appropriate healing time
        is_another_check = False
        another_another_check = False
        if self.decision == 1:
            if Person.num_of_used_bed >= K:
                is_another_check = True
            else:
                random_time = random.expovariate(mu1)
                current_time = self.env.now
                time_interval = (Person.last_time, current_time)
                bed_list[Person.num_of_used_bed].append(time_interval)
                Person.last_time = current_time
                Person.num_of_used_bed += 1
        elif self.decision == 2:
            random_time = random.expovariate(mu2)
        else:
            if Person.num_of_used_bed < K:
                another_another_check = True
            else:
                random_time = random.expovariate(mu3)
        # there might be unappropriate assign operation because of the thread //asynchronous operations. These portion of code checks it again
        if is_another_check:
            random_time = random.expovariate(mu3)
            self.decision = 3
        if another_another_check:
            random_time = random.expovariate(mu1)
            current_time = self.env.now
            time_interval = (Person.last_time, current_time)
            bed_list[Person.num_of_used_bed].append(time_interval)
            Person.last_time = current_time
            Person.num_of_used_bed += 1
            self.decision = 1

        # if we did not write enoguh events, we should document it
        if Person.written < 10000:
            Person.written += 1
            print('%d\t%s\t%g\t%d\t%d\t%d\tA' % (self.written, self.name, self.env.now, self.num_of_sick, self.num_of_used_bed, self.decision))

        # simpy should assign timeout of the current event which is the healing //process of a person
        yield self.env.timeout(random_time)
        # after required time passed,we should state the current healing time of
        # this time
        service_times.append(env.now-self.arrival_t)

        # after treatment number of sick people is decreased by one
        Person.num_of_sick -= 1

        # if a person is treated in hospital we should state the necessary info in our list
        if self.decision == 1:
            current_time = self.env.now
            time_interval = (Person.last_time, current_time)
            bed_list[Person.num_of_used_bed].append(time_interval)
            Person.last_time = current_time
            Person.num_of_used_bed -= 1
        # if we did not write enoguh events, we should document it
        if Person.written < 10000:
            Person.written += 1
            print('%d\t%s\t%g\t%d\t%d\t%d\tD' % (self.written, self.name, self.env.now, self.num_of_sick, self.num_of_used_bed, self.decision))


# generation of sick people
def people_generator(env, already_number):
    # given lambda in our documentation
    lambd = 1/300
    start_time = env.now
    # count of sick people
    count = 0
    # regulation of k
    if already_number > K:
        already_number = K
    # creation of next events concurrently
    while env.now <= finish_time+start_time:
        # if the hospital starts with admitted sick people we generate them all at time 0
        if already_number > 0:
            already_number -= 1
            count += 1
            human = Person("P%s" %(count), env, 1)
            continue
        # treatment way of sick person
        decision = random.uniform(0, 1)
        if decision < 0.2 and Person.num_of_used_bed < K:
            decision = 1
        elif decision < 0.2:
            decision = 3
        else:
            decision = 2
        # we should state the timeout value as interarrival time
        yield env.timeout(random.expovariate(N*lambd))
        count += 1
        human = Person('P%s' %(count), env, decision)

# declaration of our environment and its parameters
env = simpy.Environment()
operator = simpy.Resource(env, capacity=1)
env.process(people_generator(env, 0))
env.run()

# calculates probability of the hospital being empty
def prob_of_being_empty():
    neu = []
    for k in bed_list[0]:
        neu.append(k[1]-k[0])
    result_zeros = sum(neu)
    return result_zeros/finish_time

# calculates sample mean and sample variance of occupied beds
def avg_sampvar_occupied_beds():
    neu = []
    for k in range(len(bed_list)):
        time_length = 0
        for i in bed_list[k]: # bed_list[x] represents the time intervals of x beds being used
            time_length += i[1] - i[0]
        neu.append(time_length*k)
    avg_occupied = sum(neu) / finish_time
    x = 0
    for i, bed in enumerate(bed_list):
        sum_time = 0
        for c in bed:
            sum_time += c[1] - c[0]
        avgTime = sum_time / finish_time
        x += (avg_occupied - i)**2 * avgTime
    return avg_occupied, x

# calculates average proportion of sick people on population
def avg_prop_of_sick_on_population():
    result = sum(service_times)
    return (result/finish_time)/N # result/finish_time = avg people in the system(avg sick ppl)
    #if we divide it with N we get the proportion of sick ppl

# calculates total average sickness time
def total_avg_sickness_time():
    avg_sickness = sum(service_times) / len(service_times)
    temp = 0
    for i in range(len(service_times)):
       temp += pow(service_times[i] - avg_sickness, 2)
    sample_var_sickness = temp / (len(service_times)-1)
    return avg_sickness, sample_var_sickness
    # we find sample mean and sample variance of duration of sickness times because we do not keep
    # individual sickness records

# print statemenets
print(prob_of_being_empty())
x = avg_sampvar_occupied_beds()
print(x[0])
print(x[1])
print(avg_prop_of_sick_on_population())
print(total_avg_sickness_time())

