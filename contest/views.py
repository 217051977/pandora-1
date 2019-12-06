import os
import uuid
import subprocess
import datetime
import sys
import csv

from .forms import SignUpForm, AtemptModelForm, TeamModelForm, TeamMemberForm, TeamMemberApprovalForm, \
    CreateContestModelForm
from .models import Contest, Test, Classification, Team, TeamMember, Atempt, SafeExecError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash, logout  # last 2 imported
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files import File
from django.db.models import Max
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import smart_text
from django.utils import timezone
from django.views.generic.edit import FormView
from subprocess import check_output, CalledProcessError


# get functions
def get_user_team(request, contest_id):
    qs = TeamMember.objects.filter(team__contest=contest_id, user=request.user).first()

    if not qs:
        return Team.objects.none(), TeamMember.objects.none()

    team_obj = qs.team
    members = team_obj.teammember_set.all()

    return team_obj, members


def get_team_attempts(team):
    members_ids = team.teammember_set.values_list('user__id', flat=True).distinct()
    if not members_ids:
        return None

    return Atempt.objects.filter(contest=team.contest, user__in=members_ids).order_by('-date')


# check output function
def check_output(command, cwd):
    print('cwd = ' + cwd)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True, cwd=cwd)
    output = process.communicate()
    retcode = process.poll()
    return output, retcode


# exec functions
def exec_command(test, contest, submition_dir, obj_file, user_output, user_report):
    if test.override_exec_options:
        cpu = test.cpu
        mem = test.mem
        space = test.space
        minuid = test.minuid
        maxuid = test.maxuid
        core = test.core
        nproc = test.nproc
        fsize = test.fsize
        stack = test.stack
        clock = test.clock
    else:
        cpu = contest.cpu
        mem = contest.mem
        space = contest.space
        minuid = contest.minuid
        maxuid = contest.maxuid
        core = contest.core
        nproc = contest.nproc
        fsize = contest.fsize
        stack = contest.stack
        clock = contest.clock

    exec_cmd = os.path.join(settings.MEDIA_ROOT, "safeexec")
    exec_cmd += " --cpu %d " % cpu
    exec_cmd += "--mem %d " % mem
    exec_cmd += "--space %d " % space
    exec_cmd += "--minuid %d " % minuid
    exec_cmd += "--maxuid %d " % maxuid
    exec_cmd += "--core %d " % core
    exec_cmd += "--nproc %d " % nproc
    exec_cmd += "--fsize %d " % fsize
    exec_cmd += "--stack %d " % stack
    exec_cmd += "--clock %d " % clock
    exec_cmd += "--usage %s " % user_report
    exec_cmd += "--exec "
    exec_cmd += obj_file + ' ' + str(test.run_arguments) + ' < ' + test.input_file.path + ' > ' + user_output

    return exec_cmd


# handle functions
def handle_zip_file(atempt, f, contest):
    src_path = os.path.abspath(f.path)
    src_base = os.path.basename(src_path)
    submition_dir = os.path.dirname(src_path)

    my_cmd = 'unzip ' + src_path
    print('extraction: ' + my_cmd)
    output, ret = check_output(my_cmd, submition_dir)

    return


def handle_uploaded_file(atempt, f, contest):
    safeexec_errors = SafeExecError.objects.all()
    safeexec_ok = SafeExecError.objects.get(description='OK')
    src_path = os.path.abspath(f.path)
    src_base = os.path.basename(src_path)
    (src_name, ext) = os.path.splitext(src_base)

    print('ext: ' + ext)
    if ext == '.zip':
        handle_zip_file(atempt, f, contest)

    print('source path = ' + src_path)

    submition_dir = os.path.dirname(src_path)
    obj_file = submition_dir + '/' + src_name + '.user.o'

    print('submition dir = ' + submition_dir)

    atempt.compile_error = False
    # my_cmd = 'gcc ' + contest.compile_flags + ' ' + src_base + ' -o ' + obj_file + ' ' + contest.linkage_flags
    my_cmd = 'gcc ' + contest.compile_flags + ' ' + submition_dir + '/*.c ' + ' -I ' + submition_dir + '/src/*.c ' + ' -o ' + obj_file + ' ' + contest.linkage_flags

    print('compilation: ' + my_cmd)
    output, ret = check_output(my_cmd, submition_dir)

    if output[0] != '':
        atempt.compile_error = True
        atempt.error_description = output[0]
        print('compile error... terminating...')
        atempt.save()
        return  # if compilation errors or warnings dont bother with running the tests

    test_set = contest.test_set.all()
    n_tests = test_set.count()
    mandatory_failed = False
    pct = 0
    atempt.time_benchmark = 2147483647
    atempt.memory_benchmark = 2147483647
    atempt.cpu_time = 99999.999
    atempt.elapsed_time = 2147483647

    for test in test_set:
        record = Classification()
        record.attempt = atempt
        record.test = test
        record.passed = True

        testout_base = os.path.basename(test.output_file.path)
        (testout_name, ext) = os.path.splitext(testout_base)
        user_output = os.path.join(submition_dir, testout_base + '.user')
        user_report = os.path.join(submition_dir, testout_name + '.report')

        exec_cmd = exec_command(test, contest, submition_dir, obj_file, user_output, user_report)

        print('exec cmd is:\n')
        print(exec_cmd)

        timeStarted = datetime.datetime.now()  # Save start time.
        check_output(exec_cmd, submition_dir)
        record.execution_time = (datetime.datetime.now() - timeStarted).microseconds  # Get execution time.

        # save files
        f = open(user_report, "r")
        lines = f.readlines()
        f.close()

        f = open(user_report)
        record.report_file.save(user_report, File(f))
        f.close()

        f = open(user_output)
        record.output.save(user_output, File(f))
        f.close()

        # verify safeexec report
        safeexec_error_description = lines[0][:-1]

        se_obj = SafeExecError.objects.get(description='Other')
        for e in safeexec_errors:
            if e.description in safeexec_error_description:
                se_obj = e
                break

        record.error = se_obj
        record.error_description = safeexec_error_description
        print(safeexec_error_description)

        # lines[1] = elapsed time: 2 seconds
        # lines[2] = memory usage: 1424 kbytes
        # lines[3] = cpu usage: 1.000 seconds
        elapsed = lines[1].split(" ")
        memory = lines[2].split(" ")
        cpu = lines[3].split(" ")
        record.memory_usage = int(memory[2])
        record.cpu_time = float(cpu[2])
        record.elapsed_time = int(elapsed[2])

        if record.error != safeexec_ok:
            record.passed = False
            record.save()
            continue

        # uses the diff tool
        diff, ret = check_output('diff -B --ignore-all-space ' + user_output + ' ' + test.output_file.path,
                                 submition_dir)

        record.passed = diff[0] == ''

        if contest.automatic_weight:
            test.weight_pct = round(100 / n_tests, 2)
            test.save()

        if record.passed:
            pct += test.weight_pct
            print('test passed pct = ' + str(test.weight_pct))
            print('accumulated pct = ' + str(pct))

            if test.use_for_time_benchmark:
                atempt.time_benchmark = record.execution_time
                atempt.cpu_time = record.cpu_time
                atempt.elapsed_time = record.elapsed_time

            if test.use_for_memory_benchmark:
                atempt.memory_benchmark = record.memory_usage
        else:
            record.error_description = 'Wrong Answer'
            if test.mandatory:
                mandatory_failed = True

        record.save()

    print('obtained pct = ' + str(pct))
    print('max_class = ' + str(contest.max_classification))

    atempt.grade = (round(pct / 100 * contest.max_classification, 0), 0)[mandatory_failed]
    atempt.save()


# @login_required functions
# admin
@login_required
def admin_contest_creation(request):
    template_name = 'contest/contest_creation.html'

    form = CreateContestModelForm(request.POST or None, request.FILES or None)  # , request.FILES or None)
    print(form.is_valid())
    if form.is_valid():
        obj = form.save(commit=False)
        obj.save()
        # print(form.in_files.path)
        # form = CreateContestModelForm()
        # handle_uploaded_file(obj, obj.file, contest_obj) # to check the ins and outs files
    context = ({'form': form})

    return render(request, template_name, context)


@login_required
def admin_view(request, id):
    template_name = 'contest/admin_view.html'

    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    teams = Team.objects.filter(contest__id=id)  # get all teams associated with this contest

    for obj in teams:
        obj.members = TeamMember.objects.filter(team=obj)
        obj.room_left = obj.contest.max_team_members - obj.members.count()

    context.update({'teams': teams})

    # TODO Make it better
    query = "Select ca.id, c.name as team_name, ca.grade as team_grade, maxs.atempts as team_atempts" \
            "	from (" \
            "		select max(id) as id, count(id) as atempts, team_id" \
            "			from contest_atempt" \
            "				where contest_id = " + str(contest_obj.id) + " " \
                                                                          "					group by team_id" \
                                                                          "	) maxs" \
                                                                          "		inner join contest_atempt ca on ca.id = maxs.id " \
                                                                          "		join contest_team c on ca.team_id = c.id" \
                                                                          "		join auth_user au on ca.user_id = au.id"

    grades = Atempt.objects.raw(query)

    context.update({'grades': grades})

    # TODO Make it better
    query = "SELECT ca.id, maxs.team_atempts, maxs.team_id, au.username as username, au.first_name, au.last_name, umax.atempts as user_atempts" \
            "	FROM (" \
            "		select max(id) as id, count(id) as team_atempts, team_id" \
            "			from contest_atempt" \
            "				where contest_id = " + str(contest_obj.id) + " " \
                                                                          "					group by team_id" \
                                                                          "	) maxs" \
                                                                          "		inner join contest_atempt ca on ca.id = maxs.id" \
                                                                          "		join contest_teammember ct on ct.team_id = ca.team_id" \
                                                                          "		join contest_team c on ca.team_id = c.id" \
                                                                          "		join auth_user au on au.id = ct.user_id" \
                                                                          "		join (" \
                                                                          "			select max(id) as id, count(id) as atempts, user_id" \
                                                                          "				from contest_atempt" \
                                                                          "					where contest_id = 1" \
                                                                          "						group by user_id" \
                                                                          "		) umax on umax.user_id = ct.user_id" \
                                                                          "			order by atempts asc"

    atempts = Atempt.objects.raw(query)

    context.update({'atempts': atempts})

    form = TeamMemberForm(request.POST or None)

    if form.is_valid():
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'status/'))

    context.update({'form': form})

    return render(request, template_name, context)


# attempt
@login_required
def attempt_list_view(request, id):
    template_name = 'contest/atempt_list.html'

    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    team_obj, members = get_user_team(request, contest_obj.id)

    atempts = get_team_attempts(team_obj)

    if atempts:
        context.update({'number_of_submitions': atempts.count()})
        context.update({'last_classification': atempts.first().grade})
        context.update({'last_execution_time': atempts.first().time_benchmark})
        context.update({'last_memory_usage': atempts.first().memory_benchmark})
    else:
        context.update({'number_of_submitions': 0})
        context.update({'last_classification': 0})
        context.update({'last_execution_time': int(sys.maxsize)})
        context.update({'last_memory_usage': int(sys.maxsize)})

    team_obj.members = members
    context.update({'team': team_obj})
    context.update({'atempts': atempts})
    context.update({'maxsize': int(sys.maxsize)})

    return render(request, template_name, context)


@login_required
def attempt_view(request, id):
    template_name = 'contest/atempt_detail.html'

    atempt_obj = get_object_or_404(Atempt, id=id)
    contest_obj = atempt_obj.contest

    qs = TeamMember.objects.filter(team__contest=contest_obj.id, user=atempt_obj.user).first()
    if not qs:
        raise Http404

    team = qs.team
    team_members = team.teammember_set.all()

    # check if request.user is a member of atempt team
    if not team.teammember_set.get(user=request.user, approved=True):
        raise Http404

    results = atempt_obj.classification_set.all()
    n_tests = contest_obj.test_set.count()
    n_mandatory = contest_obj.test_set.filter(mandatory=True).count()
    n_general = n_tests - n_mandatory
    n_passed = atempt_obj.classification_set.filter(passed=True).count()
    mandatory_passed = atempt_obj.classification_set.filter(passed=True, test__mandatory=True).count()
    general_passed = atempt_obj.classification_set.filter(passed=True, test__mandatory=False).count()

    print('number of results ' + str(results.count()))
    print('number of tests ' + str(n_tests))
    print('number of mandatory tests ' + str(n_mandatory))
    print('number of general tests ' + str(n_general))
    print('number of general passed tests ' + str(general_passed))
    print('number of mandatory passed tests ' + str(mandatory_passed))

    for res in results:
        res.expected_output = smart_text(res.test.output_file.read(), encoding='utf-8', strings_only=False,
                                         errors='strict')
        res.obtained_output = smart_text(res.output.read(), encoding='utf-8', strings_only=False, errors='strict')

    context = {'contest': contest_obj}
    context.update({'team': team})
    context.update({'team_members': team_members})
    context.update({'atempt': atempt_obj})
    context.update({'maxsize': 2147483647})
    context.update({'n_passed': n_passed})
    context.update({'n_total': n_tests})
    context.update({'mandatory_passed': mandatory_passed})
    context.update({'mandatory_total': n_mandatory})
    context.update({'general_passed': general_passed})
    context.update({'n_general': n_general})
    context.update({'results': results})

    return render(request, template_name, context)


@login_required
def attempt_create_view(request, id):
    template_name = 'contest/contest_form.html'
    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}
    can_submit = True

    present = timezone.now()
    # present = datetime.datetime.now()
    if present < contest_obj.start_date or present > contest_obj.end_date:
        # contest is not opened
        return redirect(os.path.join(contest_obj.get_absolute_url()))

    team_obj, members = get_user_team(request, contest_obj.id)
    if not team_obj:
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'team/join/'))

    atempts = get_team_attempts(team_obj)

    if contest_obj.max_submitions > 0:
        if atempts and atempts.count() >= contest_obj.max_submitions:
            messages.error(request, "You have reached the maximum number of submitions for this contest.")
            can_submit = False

    if not contest_obj.is_open:
        messages.error(request, "This contest is not active.")
        can_submit = False

    if not team_obj.active or not members.filter(user=request.user).first().approved or not request.user.profile.valid:
        messages.error(request,
                       "You need to be an Active member and approved member of an active team to make submitions")
        can_submit = False

    form = AtemptModelForm(request.POST or None, request.FILES or None)
    if can_submit and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.contest = contest_obj
        obj.team = team_obj
        obj.save()
        handle_uploaded_file(obj, obj.file, contest_obj)
        return redirect(obj.get_absolute_url())

    context.update({'form': form})
    return render(request, template_name, context)


# change password
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'form.html', {'title': 'Change Password', 'form': form, 'button': 'submit'})


# extract grades
def extract_grades(request, id):
    # get the contest
    contest_obj = get_object_or_404(Contest, id=id)

    # create the HttpResponse object with the appropriate csv header.

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename = "Contest_"' + str(
        contest_obj.id) + '""' + contest_obj.short_name + '".csv"'

    # get the values needed to be inserted in the csv
    # TODO: making this SQL sector

    query = "SELECT ca.id, cp.number as student_number, au.first_name as student_first_name, au.last_name as student_last_name, c.name as team_name, ca.grade, maxs.team_atempts, umax.atempts as userAtempts " \
            "   FROM (" \
            "       select max(id) as id, count(id) as team_atempts, team_id" \
            "           from contest_atempt" \
            "               where contest_id = 1" \
            "                   group by team_id" \
            "   ) maxs" \
            "       inner join contest_atempt ca on ca.id = maxs.id" \
            "       join contest_teammember ct on ct.team_id = ca.team_id" \
            "       join contest_team c on ca.team_id = c.id" \
            "       join auth_user au on au.id = ct.user_id" \
            "       join (" \
            "           select max(id) as id, count(id) as atempts, user_id" \
            "               from contest_atempt" \
            "                   where contest_id = 1" \
            "                       group by user_id" \
            "       ) umax on umax.user_id = ct.user_id" \
            "       join contest_profile cp on au.id = cp.user_id order by number asc"

    grades = Atempt.objects.raw(query)

    writer = csv.writer(response)

    writer.writerow(['Student Number', 'Student Name', 'team', 'Grade', 'Student Atempts', 'Team Atempts'])

    for g in grades:
        writer.writerow([g.student_number,
                         g.student_first_name + ' ' + g.student_first_name,
                         g.team_name,
                         g.grade,
                         g.userAtempts,
                         g.team_atempts])
    # make a row splited by comas
    # writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    # writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response


# contest
@login_required
def contest_list_view(request):
    #	if not request.user.is_active:
    #		return redirect('not_active')
    template_name = 'contest/list.html'

    contests_qs = Contest.objects.filter(visible=True)
    qs = TeamMember.objects.select_related('team').filter(user=request.user)

    context = {'object_list': contests_qs,
               'team_contests': qs,
               'title': 'Welcome to PANDORA',
               'description': 'PANDORA is an Automatic Assement Tool.'}
    return render(request, template_name, context)


@login_required
def contest_detail_view(request, id):
    obj = get_object_or_404(Contest, id=id)

    present = timezone.now()
    if present < obj.start_date:
        # contest is not yet open. Don't let anyone see a dam thing.
        template_name = 'contest/closed.html'
    else:
        template_name = 'contest/detail.html'

    context = {"contest": obj}
    return render(request, template_name, context)


# profile
@login_required
def profile_view(request):
    template_name = 'contest/profile.html'
    context = {'user': request.user}
    return render(request, template_name, context)


# ranking
@login_required
def ranking_view(request, id):
    template_name = 'contest/ranking.html'

    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    # TODO Make it better
    query = "SELECT ca.*, maxs.atempts, maxs.team_id FROM (" \
            "select max(id) as id," \
            "count(id) as atempts," \
            "team_id from " \
            "contest_atempt" \
            " where contest_id = " + str(contest_obj.id) + " group by team_id)" \
                                                           "maxs inner join contest_atempt ca on ca.id = maxs.id" \
                                                           " order by grade desc, atempts asc, time_benchmark asc, memory_benchmark asc, elapsed_time asc, cpu_time asc"
    # select contest_atempt.id as id, max(date), grade, count(contest_atempt.id) as number_of_atempts, time_benchmark, memory_benchmark elapsed_time, cpu_time from contest_atempt where contest_id = " + str(contest_obj.id) + " group by (team_id) order by grade desc, time_benchmark asc, memory_benchmark asc, number_of_atempts asc"

    atempts = Atempt.objects.raw(query)

    context.update({'atempts': atempts})
    context.update({'maxsize': int(sys.maxsize)})
    return render(request, template_name, context)


# team
@login_required
def team_create_view(request, id):
    template_name = 'contest/contest_form.html'
    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    teams = Team.objects.filter(contest__id=id)  # get all teams associated with this contest
    user_team = TeamMember.objects.select_related('team').filter(team__contest=contest_obj.id,
                                                                 user=request.user).first()

    if user_team:
        print('this user already has a team...')
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'myteam/'))

    form = TeamModelForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.contest = contest_obj
        obj.save()
        team_member_obj = TeamMember()
        team_member_obj.user = request.user
        team_member_obj.approved = True
        team_member_obj.team = obj
        team_member_obj.save()
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'myteam/'))

    context.update({'form': form})
    context.update({"title": 'Create New Team'})
    return render(request, template_name, context)


@login_required
def team_detail_view(request, id):
    template_name = 'contest/team_detail.html'

    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    # qs = TeamMember.objects.select_related('team').filter(team__contest = contest_obj.id, user = request.user).first()
    team_obj, members = get_user_team(request, contest_obj.id)
    if not team_obj:
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'team/join/'))

    team_member_obj = TeamMember.objects.get(team=team_obj, user=request.user)

    can_be_deleted = True
    if members.count() > 1 or not team_member_obj.approved or get_team_attempts(team_obj):
        can_be_deleted = False

    form = TeamMemberApprovalForm(request.POST or None)
    if form.is_valid():
        if "team_delete" in request.POST and can_be_deleted:
            team_member_obj.delete()
            team_obj.delete()
            return redirect(os.path.join(contest_obj.get_absolute_url(), 'team/join/'))

        if team_member_obj.approved:
            if "member_id" in request.POST:
                team_member_obj2 = TeamMember.objects.get(id=form.cleaned_data.get("member_id"))
                team_member_obj2.approved = True
                team_member_obj2.save()

        if members.count() > 1 and "member_id_remove" in request.POST:
            team_member_obj2 = TeamMember.objects.get(id=form.cleaned_data.get("member_id_remove"))
            if (team_member_obj2 == team_member_obj and not team_member_obj2.approved) or team_member_obj.approved:
                team_member_obj2.delete()
                return redirect(os.path.join(contest_obj.get_absolute_url(), 'team/join/'))

        form = TeamMemberApprovalForm()
        team_obj.members = team_obj.teammember_set.all()

    team_obj.members = team_obj.teammember_set.all()

    context.update({'team': team_obj})
    context.update({'can_delete': can_be_deleted})  # it it only has one member, it can be deleted
    context.update({'can_approve': team_member_obj.approved})  # it it only has one member, it can be deleted
    context.update({'form': form})
    return render(request, template_name, context)


@login_required
def team_join_view(request, id):
    template_name = 'contest/team_join.html'
    contest_obj = get_object_or_404(Contest, id=id)
    context = {'contest': contest_obj}

    user_team, members = get_user_team(request, contest_obj.id)
    user_team.members = members
    # TeamMember.objects.select_related('team').filter(team__contest = contest_obj.id, user = request.user).first()

    if user_team:
        return redirect(os.path.join(contest_obj.get_absolute_url(), 'myteam/'))

    # get all teams active in this contenst
    teams = Team.objects.filter(contest__id=id)  # get all teams associated with this contest

    # set the members details and the amount of new member that can join
    for obj in teams:
        obj.members = TeamMember.objects.filter(team=obj)
        obj.room_left = obj.contest.max_team_members - obj.members.count()

    # update the contenxt to send to the team_join.html
    context.update({'teams': teams})

    # no idea what it does
    form = TeamMemberForm(request.POST or None)

    if form.is_valid():
        team_id = form.cleaned_data.get("team_id")
        team_member = TeamMember()

        team = Team.objects.get(id=team_id)

        qs = team.teammember_set.all()
        if (qs.count() > team.contest.max_team_members):
            messages.error(request, "Error! This team can not accept new members")
        else:
            team_member.team = team
            team_member.user = request.user
            team_member.approved = False
            team_member.save()
            return redirect(os.path.join(contest_obj.get_absolute_url(), 'myteam/'))
        form = TeamMemberForm()

    # context.update({'form': form})
    return render(request, template_name, context)


def pagelogout(request):
    if request.method == "POST":
        logout(request)
        return redirect('home')


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.number = form.cleaned_data.get('number')
            user.profile.gprd = form.cleaned_data.get('gprd')
            user.profile.valid = False
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()

    context = {'form': form,
               'title': 'Register'}
    return render(request, 'form.html', context)


def notactive_view(request):
    template_name = 'contest/error.html'
    context = {'title': 'Welcome to PANDORA',
               'description': 'Your account is not active. Please wait for the administrator to activate your account.'}
    return render(request, template_name, context)
