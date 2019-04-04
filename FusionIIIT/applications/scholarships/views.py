# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

# Create your views here.
# from django.shortcuts import render

import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
# Create your views here.
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.models import User
from applications.academic_information.models import Spi, Student
from applications.globals.models import (Designation, ExtraInfo,
                                         HoldsDesignation)

from .models import (Award_and_scholarship, Constants, Director_gold,
                     Director_silver, Mcm, Notional_prize, Previous_winner,
                     Proficiency_dm, Release, Notification)

from notification.views import scholarship_portal_notif
# Create your views here.


@login_required(login_url='/accounts/login')
def spacs(request):
    # Arihant:Student either accepts or Declines the Award Notification
    if request.method == 'POST':
        if 'studentapprovesubmit' in request.POST:
            award = request.POST.get('studentapprovesubmit')
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            if award=='Mcm Scholarship':
                request.session['last_clicked']='studentapprovesubmit_mcm'
                x.notification_mcm_flag=False
                x.invite_mcm_accept_flag=True
                print('mcm accepted')
            else:
                request.session['last_clicked']='studentapprovesubmit_con'
                x.notification_convocation_flag=False
                x.invite_covocation_accept_flag=True
            x.save()
        if 'studentdeclinesubmit' in request.POST:
            award = request.POST.get('studentdeclinesubmit')
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            if award=='Mcm Scholarship':
                x.notification_mcm_flag=False
                x.invite_mcm_accept_flag=False
            else:
                x.notification_convocation_flag=False
                x.invite_covocation_accept_flag=False
            x.save()
    convener = Designation.objects.get(name='spacsconvenor')
    assistant = Designation.objects.get(name='spacsassistant')
    hd = HoldsDesignation.objects.filter(user=request.user,designation=convener)
    hd1 = HoldsDesignation.objects.filter(user=request.user,designation=assistant)
    if request.user.extrainfo.user_type == 'student':
        return HttpResponseRedirect('/spacs/student_view')
    elif hd:
        return HttpResponseRedirect('/spacs/convener_view')
    elif hd1:
        return HttpResponseRedirect('/spacs/staff_view')
    else:
        return HttpResponseRedirect('/spacs/stats')# Arihant:this view is for the other members of the college



@login_required(login_url='/accounts/login')
def convener_view(request):
    if request.method == 'POST':
        if 'Submit' in request.POST:
            award = request.POST.get('type')
            programme = request.POST.get('programme')
            batch = request.POST.get('batch')
            from_date = request.POST.get('From')
            to_date = request.POST.get('To')
            remarks = request.POST.get('remarks')
            request.session['last_clicked']='Submit'


            Release.objects.create(
                startdate=from_date,
                enddate=to_date,
                award=award,
                remarks=remarks,
                batch=batch,
                notif_visible=1,
                award_form_visible=0
            )
            # Arihant:It updates the student Notification table on the spacs head sending the mcm invitation
            if batch == 'all':
                #Notification starts
                convenor = request.user
                receipent1 = Student.objects.filter(programme = programme)
                for student in receipent1:
                    scholarship_portal_notif(convenor,student.id.user, 'award-' + award)
                #Notification ends
                if award == 'Mcm Scholarship':
                    res = Notification.objects.filter(student_id__programme=programme).update(notification_mcm_flag=True)
                else:
                    res = Notification.objects.filter(student_id__programme=programme).update(notification_convocation_flag=True)
            else:
                #Notification starts
                convenor = request.user
                receipent1 = Student.objects.filter(programme = programme,id__id__startswith=batch)
                for student in receipent1:
                    scholarship_portal_notif(convenor,student.id.user, 'award-' + award)
                #Notification ends
                if award == 'Mcm Scholarship':
                    res = Notification.objects.filter(student_id__programme=programme,student_id__id__id__startswith=batch).update(notification_mcm_flag=True)
                else:
                    res = Notification.objects.filter(student_id__programme=programme,student_id__id__id__startswith=batch).update(notification_convocation_flag=True)



            messages.success(request,award+' are invited successfully')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Email' in request.POST:
            year = request.POST.get('year')
            spi = request.POST.get('spi')
            cpi = request.POST.get('cpi')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            Notional_prize.objects.create(
                year=year,
                spi=spi,
                cpi=cpi,
                award_id=award_id
            )
            messages.success(request,award+' are invited successfully')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_mcm' in request.POST:
            pk = request.POST.get('id')
            award = Mcm.objects.get(id=pk).award_id
            student_id = Mcm.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Mcm.objects.filter(id=pk).update(status='Accept')
            request.session['last_clicked']='Accept_mcm'
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Accept_mcm')
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            student_id = Mcm.objects.get(id=pk).student
            Mcm.objects.filter(id=pk).update(status='Reject')
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Reject_mcm')
            messages.success(request,'Application is rejected')
            request.session['last_clicked']='Reject_mcm'
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_gold' in request.POST:
            pk = request.POST.get('id')
            award = Director_gold.objects.get(id=pk).award_id
            student_id = Director_gold.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Director_gold.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Accept_gold')
            request.session['last_clicked']='Accept_gold'
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_gold.objects.get(id=pk).student
            Director_gold.objects.filter(id=pk).update(status='Reject')
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Reject_gold')
            request.session['last_clicked']='Reject_gold'
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')

        elif 'Accept_silver' in request.POST:
            pk = request.POST.get('id')
            award = Director_silver.objects.get(id=pk).award_id
            student_id = Director_silver.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Director_silver.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Accept_silver')
            request.session['last_clicked']='Accept_silver'
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            student_id = Director_silver.objects.get(id=pk).student
            Director_silver.objects.filter(id=pk).update(status='Reject')
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Reject_silver')
            request.session['last_clicked']='Reject_silver'
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Accept_dm' in request.POST:
            pk = request.POST.get('id')
            award = Proficiency_dm.objects.get(id=pk).award_id
            student_id = Proficiency_dm.objects.get(id=pk).student
            year = datetime.datetime.now().year
            Proficiency_dm.objects.filter(id=pk).update(status='Accept')
            Previous_winner.objects.create(
                student=student_id,
                year=year,
                award_id=award
            )
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Accept_dm')
            request.session['last_clicked']='Accept_dm'
            messages.success(request,'Application is accepted')
            return HttpResponseRedirect('/spacs/convener_view')
        elif 'Reject_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            student_id = Proficiency_dm.objects.get(id=pk).student
            convenor = request.user
            receipent = student_id
            scholarship_portal_notif(convenor,receipent.id.user,'Reject_dm')
            request.session['last_clicked']='Reject_dm'
            messages.success(request,'Application is rejected')
            return HttpResponseRedirect('/spacs/convener_view')


    else:
        mcm = Mcm.objects.all()
        #mcm = Mcm.objects.all().order_by('annual_income').rever
        ch = Constants.batch
        source = Constants.father_occ_choice
        time = Constants.time
        release = Release.objects.all()
        notification = Notification.objects.all()
        winners = Previous_winner.objects.all()
        spi = Spi.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)

        last_clicked=''
        try:
            last_clicked = request.session['last_clicked']
            del request.session['last_clicked']
        except:
            print('last_clicked not found')

        context={'mcm': mcm, 'source': source, 'time': time, 'ch': ch, 'awards': awards,
                   'spi': spi, 'student': student, 'winners': winners, 'release': release,
                   'gold': gold, 'silver': silver, 'dandm': dandm, 'con': con, 'assis': assis,
                    'hd': hd, 'hd1': hd1,'last_clicked':last_clicked
                   }
        return render(request, 'scholarshipsModule/scholarships_convener.html',context)


@login_required(login_url='/accounts/login')
def student_view(request):
    if request.method == 'POST':
        if 'Submit_mcm' in request.POST:
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            x.invite_mcm_accept_flag=False
            x.save()
            father_occ = request.POST.get('father_occ')
            mother_occ = request.POST.get('mother_occ')
            brother_name = request.POST.get('brother_name')
            sister_name = request.POST.get('sister_name')
            brother_occupation = request.POST.get('brother_occupation')
            sister_occupation = request.POST.get('sister_occupation')
            income_father = int(request.POST.get('father_income'))
            income_mother = int(request.POST.get('mother_income'))
            income_other = int(request.POST.get('other_income'))
            father_occ_desc = request.POST.get('father_occ_desc')
            mother_occ_desc = request.POST.get('mother_occ_desc')
            four_wheeler = request.POST.get('four_wheeler')
            four_wheeler_desc = request.POST.get('four_wheeler_desc')
            two_wheeler_desc = request.POST.get('two_wheeler_desc')
            two_wheeler = request.POST.get('two_wheeler')
            house = request.POST.get('house')
            plot_area = request.POST.get('plot_area')
            constructed_area = request.POST.get('constructed_area')
            school_fee = request.POST.get('school_fee')
            school_name = request.POST.get('school_name')
            college_fee = request.POST.get('college_fee')
            college_name = request.POST.get('college_name')
            loan_amount = request.POST.get('loan_amount')
            bank_name = request.POST.get('bank_name')
            income_certificate = request.FILES.get('income_certificate')
            student = request.user.extrainfo.student
            annual_income = income_father + income_mother + income_other
            a = Award_and_scholarship.objects.get(award_name="Mcm").id
            award_id = Award_and_scholarship.objects.get(id=a)
            Mcm.objects.create(
                father_occ=father_occ,
                mother_occ=mother_occ,
                brother_name=brother_name,
                sister_name=sister_name,
                income_father=income_father,
                income_mother=income_mother,
                income_other=income_other,
                brother_occupation=brother_occupation,
                sister_occupation=sister_occupation,
                student=student,
                annual_income=annual_income,
                income_certificate=income_certificate,
                award_id=award_id,
                father_occ_desc=father_occ_desc,
                mother_occ_desc=mother_occ_desc,
                four_wheeler=four_wheeler,
                four_wheeler_desc=four_wheeler_desc,
                two_wheeler_desc=two_wheeler_desc,
                two_wheeler=two_wheeler,
                house=house,
                plot_area=plot_area,
                constructed_area=constructed_area,
                school_fee=school_fee,
                school_name=school_name,
                bank_name=bank_name,
                loan_amount=loan_amount,
                college_fee=college_fee,
                college_name=college_name
            )
            request.session['last_clicked']='Submit_mcm'
            messages.success(request,'Mcm scholarhsip is successfully applied')
            return HttpResponseRedirect('/spacs/student_view')

        elif 'Submit_gold' in request.POST:
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            x.invite_covocation_accept_flag=False
            x.save()
            relevant_document = request.FILES.get('myfile')
            student_id = request.user.extrainfo.student
            a = Award_and_scholarship.objects.get(award_name="Director Gold Medal").id
            award_id = Award_and_scholarship.objects.get(id=a)
            academic_achievements = request.POST.get('academic_achievements')
            science_inside = request.POST.get('science_inside')
            science_outside = request.POST.get('science_outside')
            games_inside = request.POST.get('games_inside')
            games_outside = request.POST.get('games_outside')
            cultural_inside = request.POST.get('cultural_inside')
            cultural_outside = request.POST.get('cultural_outside')
            social = request.POST.get('social')
            coorporate = request.POST.get('coorporate')
            hall_activities = request.POST.get('hall_activities')
            gymkhana_activities = request.POST.get('gymkhana_activities')
            institute_activities = request.POST.get('institute_activities')
            counselling_activities = request.POST.get('counselling_activities')
            other_activites = request.POST.get('other_activites')
            justification = request.POST.get('justification')
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')

            Director_gold.objects.create(
                student=student_id,
                relevant_document=relevant_document,
                award_id=award_id,
                academic_achievements=academic_achievements,
                science_inside=science_inside,
                science_outside=science_outside,
                games_inside=games_inside,
                games_outside=games_outside,
                cultural_inside=cultural_inside,
                cultural_outside=cultural_outside,
                social=social,
                coorporate=coorporate,
                hall_activities=hall_activities,
                gymkhana_activities=gymkhana_activities,
                institute_activities=institute_activities,
                counselling_activities=counselling_activities,
                correspondence_address=correspondence_address,
                financial_assistance=financial_assistance,
                grand_total=grand_total,
                nearest_policestation=nearest_policestation,
                nearest_railwaystation=nearest_railwaystation,
                justification=justification
            )
            request.session['last_clicked']='Submit_gold'
            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')

        elif 'Submit_silver' in request.POST:
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            x.invite_covocation_accept_flag=False
            x.save()
            relevant_document = request.FILES.get('myfile')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            student_id = request.user.extrainfo.student
            inside_achievements = request.POST.get('inside_achievements')
            outside_achievements = request.POST.get('outside_achievements')
            justification = request.POST.get('justification')
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')

            Director_silver.objects.create(
                student=student_id,
                award_id=award_id,
                relevant_document=relevant_document,
                inside_achievements=inside_achievements,
                justification=justification,
                correspondence_address=correspondence_address,
                financial_assistance=financial_assistance,
                grand_total=grand_total,
                nearest_policestation=nearest_policestation,
                nearest_railwaystation=nearest_railwaystation,
                outside_achievements=outside_achievements
            )
            request.session['last_clicked']='Submit_silver'
            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')


        elif 'Submit_dandm' in request.POST:
            x = Notification.objects.get(student_id = request.user.extrainfo.id)
            x.invite_covocation_accept_flag=False
            x.save()
            title_name = request.POST.get('title')
            no_of_students = request.POST.get('students')
            relevant_document = request.FILES.get('myfile')
            award = request.POST.get('award')
            a = Award_and_scholarship.objects.get(award_name=award).id
            award_id = Award_and_scholarship.objects.get(id=a)
            student_id = request.user.extrainfo.student
            try:
                roll_no1 = int(request.POST.get('roll_no1'))
            except:
                roll_no1=0

            try:
                roll_no2 = int(request.POST.get('roll_no2'))
            except:
                roll_no2=0

            try:
                roll_no3 = int(request.POST.get('roll_no3'))
            except:
                roll_no3=0

            try:
                roll_no4 = int(request.POST.get('roll_no4'))
            except:
                roll_no4=0

            try:
                roll_no5 = int(request.POST.get('roll_no5'))
            except:
                roll_no5=0

            ece_topic = request.POST.get('ece_topic')
            cse_topic = request.POST.get('cse_topic')
            mech_topic = request.POST.get('mech_topic')
            design_topic = request.POST.get('design_topic')
            ece_percentage = int(request.POST.get('ece_percentage'))
            cse_percentage = int(request.POST.get('cse_percentage'))
            mech_percentage = int(request.POST.get('mech_percentage'))
            design_percentage = int(request.POST.get('design_percentage'))
            brief_description = request.POST.get('brief_description')
            justification = request.POST.get('justification')
            correspondence_address=request.POST.get('c_address')
            financial_assistance=request.POST.get('financial_assistance')
            grand_total=request.POST.get('grand_total')
            nearest_policestation=request.POST.get('nps')
            nearest_railwaystation=request.POST.get('nrs')


            Proficiency_dm.objects.create(
                title_name=title_name,
                no_of_students=no_of_students,
                student=student_id,
                award_id=award_id,
                relevant_document=relevant_document,
                roll_no1=roll_no1,
                roll_no2=roll_no2,
                roll_no3=roll_no3,
                roll_no4=roll_no4,
                roll_no5=roll_no5,
                ece_topic=ece_topic,
                cse_topic=cse_topic,
                mech_topic=mech_topic,
                design_topic=design_topic,
                ece_percentage=ece_percentage,
                cse_percentage=cse_percentage,
                mech_percentage=mech_percentage,
                design_percentage=design_percentage,
                brief_description=brief_description,
                correspondence_address=correspondence_address,
                financial_assistance=financial_assistance,
                grand_total=grand_total,
                nearest_policestation=nearest_policestation,
                nearest_railwaystation=nearest_railwaystation,
                justification=justification
            )
            request.session['last_clicked']='Submit_dm'
            messages.success(request,'Application is successfully submitted')
            return HttpResponseRedirect('/spacs/student_view')


    else:
        #start of database queries
        mcm = Mcm.objects.all()
        ch = Constants.batch
        time = Constants.time
        mother_occ = Constants.MOTHER_OCC_CHOICES
        source = Constants.father_occ_choice
        release = Release.objects.all()
        mcm_release = Release.objects.filter(award='Mcm Scholarship')
        convocation_release = Release.objects.filter(award='Convocation Medals')
        release_count = release.count()
        winners = Previous_winner.objects.all()
        spi = Spi.objects.all()
        student = Student.objects.all()
        student_batch = str(request.user.extrainfo.student)[0:4]
        awards = Award_and_scholarship.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)
        x = Notification.objects.get(student_id = request.user.extrainfo.id)

        # Arihant: Here we are fetching the flags from the Notification table of student
        #end of database queries


        #notification flags
        for dates in release:
            if check_date(dates.startdate,dates.enddate):
                print('correct date found not deleting',dates.enddate)
            else:
                print('enddate exceed deleting now',dates.enddate)
                if dates.award == "Mcm":
                    x = Notification.objects.get(student_id = request.user.extrainfo.id)
                    x.invite_mcm_accept_flag=False
                    x.save()
                else:
                    x = Notification.objects.get(student_id = request.user.extrainfo.id)
                    x.invite_covocation_accept_flag=False
                    x.save()
                Release.objects.filter(id=dates.id).delete()

        release = Release.objects.all()
        notif_mcm_flag = x.notification_mcm_flag
        #print('printing flag',notif_mcm_flag)
        notif_convocation_flag  = x.notification_convocation_flag
        show_mcm_flag=x.invite_mcm_accept_flag
        show_convocation_flag=x.invite_covocation_accept_flag
        #end

        last_clicked=''
        try:
            last_clicked = request.session['last_clicked']
            del request.session['last_clicked']
        except:
            print('last_clicked not found')

        return render(request, 'scholarshipsModule/scholarships_student.html',
                  {'mcm': mcm, 'time': time, 'ch': ch, 'awards': awards, 'spi': spi,
                   'student': student,'student_batch':student_batch, 'winners': winners, 'release': release,
                   'notif_mcm_flag':notif_mcm_flag,'notif_convocation_flag':notif_convocation_flag,'show_mcm_flag':show_mcm_flag,'show_convocation_flag':show_convocation_flag,'release_count': release_count,
                   'gold': gold, 'silver': silver, 'dandm': dandm, 'source': source,
                  'mother_occ': mother_occ, 'con': con, 'assis': assis,'hd': hd, 'hd1': hd1,'last_clicked':last_clicked})


@login_required(login_url='/accounts/login')
def staff_view(request):
    if request.method == 'POST':
        if 'Verify_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(id=pk).update(status='COMPLETE')
            request.session['last_clicked']='Verify_mcm'
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Reject_mcm' in request.POST:
            pk = request.POST.get('id')
            Mcm.objects.filter(student=pk).update(status='Reject')
            request.session['last_clicked']='Reject_mcm'
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='COMPLETE')
            request.session['last_clicked']='Verify_gold'
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Reject_gold' in request.POST:
            pk = request.POST.get('id')
            Director_gold.objects.filter(id=pk).update(status='Reject')
            request.session['last_clicked']='Reject_gold'
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='COMPLETE')
            request.session['last_clicked']='Verify_silver'
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Reject_silver' in request.POST:
            pk = request.POST.get('id')
            Director_silver.objects.filter(id=pk).update(status='Reject')
            request.session['last_clicked']='Reject_silver'
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')

        elif 'Verify_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='COMPLETE')
            request.session['last_clicked']='Verify_dm'
            messages.success(request,'Verified successfully')
            return HttpResponseRedirect('/spacs/staff_view')
        elif 'Reject_dm' in request.POST:
            pk = request.POST.get('id')
            Proficiency_dm.objects.filter(id=pk).update(status='Reject')
            request.session['last_clicked']='Reject_dm'
            messages.success(request,'Rejected successfully')
            return HttpResponseRedirect('/spacs/staff_view')
    else:
        #mcm = Mcm.objects.all().order_by('student__cpi')
        mcm = Mcm.objects.all()
        gold = Director_gold.objects.all()
        silver = Director_silver.objects.all()
        dandm = Proficiency_dm.objects.all()
        student = Student.objects.all()
        awards = Award_and_scholarship.objects.all()
        winners = Previous_winner.objects.all()
        con = Designation.objects.get(name='spacsconvenor')
        assis = Designation.objects.get(name='spacsassistant')
        hd = HoldsDesignation.objects.get(designation=con)
        hd1 = HoldsDesignation.objects.get(designation=assis)

        last_clicked=''
        try:
            last_clicked = request.session['last_clicked']
            del request.session['last_clicked']
        except:
            print('last_clicked not found')
            print('printting value',last_clicked)


        return render(request, 'scholarshipsModule/scholarships_staff.html',
                  {'mcm': mcm, 'student': student,
                   'awards': awards, 'gold': gold,
                   'silver': silver, 'dandm': dandm, 'winners': winners,
                   'con': con, 'assis': assis,'hd': hd, 'hd1': hd1,'last_clicked':last_clicked})

# Arihant: This view is created for the rest of audience excluding students, spacs convenor and spacs assistant
def stats(request):
    mcm = Mcm.objects.all()
    gold = Director_gold.objects.all()
    silver = Director_silver.objects.all()
    dandm = Proficiency_dm.objects.all()
    student = Student.objects.all()
    awards = Award_and_scholarship.objects.all()
    winners = Previous_winner.objects.all()
    con = Designation.objects.get(name='spacsconvenor')
    assis = Designation.objects.get(name='spacsassistant')
    hd = HoldsDesignation.objects.get(designation=con)
    hd1 = HoldsDesignation.objects.get(designation=assis)

    return render(request, 'scholarshipsModule/stats.html',
              {'mcm': mcm, 'student': student,
               'awards': awards, 'gold': gold,
               'silver': silver, 'dandm': dandm, 'winners': winners,
               'con': con, 'assis': assis,'hd': hd, 'hd1': hd1})





def convener_catalogue(request):
    if request.method == 'POST':
        award_name=request.POST.get('award_name')
        catalog_content=request.POST.get('catalog_content')
        context = {}
        try:
            award=Award_and_scholarship.objects.get(award_name=award_name)
            award.catalog=catalog_content
            award.save()
            context['result']='Success'
        except:
            context['result']='Failure'
        return HttpResponse(json.dumps(context), content_type='convener_catalogue/json')

    else:
        award_name=request.GET.get('award_name')
        print(award_name)
        context = {}
        try:
            award = Award_and_scholarship.objects.get(award_name=award_name)
            context['catalog']=award.catalog
            context['result'] = 'Success'
        except:
            context['result'] = 'Failure'
        return HttpResponse(json.dumps(context), content_type='convener_catalogue/json')


def get_winners(request):
    award_name = request.GET.get('award_name')
    batch_year = int(request.GET.get('batch'))
    programme_name = request.GET.get('programme')
    award = Award_and_scholarship.objects.get(award_name=award_name)
    print(award_name,award)
    print(batch_year)
    winners=Previous_winner.objects.filter(year=batch_year,award_id=award,programme=programme_name)
    context={}
    context['student_name']=[]
    context['student_program'] = []
    context['roll']=[]

# Arihant: If-Else Condition for previous winner if there is or no data in the winner table
    if winners:
        for winner in winners:

            extra_info = ExtraInfo.objects.get(id=winner.student_id)
            s_id = Student.objects.get(id=extra_info)
            s_name = extra_info.user.first_name
            s_roll = winner.student_id
            s_program=s_id.programme
            print(s_roll,type(s_roll))
            context['student_name'].append(s_name)
            context['roll'].append(s_roll)
            context['student_program'].append(s_program)

        context['result']='Success'

    else:
        context['result']='Failure'

    return HttpResponse(json.dumps(context), content_type='get_winners/json')

def get_win(request):
    acad_year = int(request.GET.get('acad_year'))
    print(acad_year)
    award = Award_and_scholarship.objects.filter(award_name='Mcm')
    winners=Previous_winner.objects.filter(year=acad_year).filter(~Q(award_id=award))
    context={}
    context['student_name']=[]
    context['student_program'] = []
    context['roll']=[]
    context['award_n']=[]

# Arihant: If-Else Condition for previous winner if there is or no data in the winner table
    if winners:
        for winner in winners:

            extra_info = ExtraInfo.objects.get(id=winner.student_id)
            s_id = Student.objects.get(id=extra_info)
            s_name = extra_info.user.first_name
            s_roll = winner.student_id
            s_program=s_id.programme
            s_award=winner.award_id.award_name
            print(s_roll,type(s_roll))
            context['student_name'].append(s_name)
            context['roll'].append(s_roll)
            context['student_program'].append(s_program)
            context['award_n'].append(s_award)

        context['result']='Success'

    else:
        context['result']='Failure'

    return HttpResponse(json.dumps(context), content_type='get_win/json')


# Arihant: Here we are extracting mcm_flag
def get_mcm_flag(request):
    print('hello get_mcm_flag')
    x = Notification.objects.get(student_id = request.user.extrainfo.id)
    x.invite_mcm_accept_flag=True
    x.notification_mcm_flag=False
    x.save()
    request.session['last_clicked']='get_mcm_flag'
    context={}
    context['show_mcm_flag']=True
    if x:
        context['result']='Success'
    else:
        context['result']='Failure'
    print('printing accept flag',x.invite_mcm_accept_flag)
    print('printing notification flag',x.notification_mcm_flag)
    return HttpResponse(json.dumps(context), content_type='get_mcm_flag/json')
    #return HttpResponseRedirect('/spacs/student_view')

# Arihant: Here we are extracting convocation_flag
def get_convocation_flag(request):
    print('hello get_convocation_flag')
    x = Notification.objects.get(student_id = request.user.extrainfo.id)
    x.invite_covocation_accept_flag=True
    x.notification_convocation_flag=False
    x.save()
    request.session['last_clicked']='get_convocation_flag'
    context={}
    context['show_convocation_flag']=True
    if x:
        context['result']='Success'
    else:
        context['result']='Failure'
    print('printing accept flag',x.invite_covocation_accept_flag)
    print('printing notification flag',x.notification_convocation_flag)
    return HttpResponse(json.dumps(context), content_type='get_convocation_flag/json')

def get_content(request):
    print('data is coming through')
    award_name=request.GET.get('award_name')
    print(award_name)
    context={}
    try:
        award = Award_and_scholarship.objects.get(award_name=award_name)
        context['result']='Success'
        context['content']=award.catalog

    except:
        context['result']='Failure'

    return HttpResponse(json.dumps(context), content_type='get_content/json')

def check_date(start_date, end_date):
    current_date = datetime.date.today()
    if start_date<end_date:
        if current_date <= end_date:
            return True
        else:
            return False
    else:
        return False
