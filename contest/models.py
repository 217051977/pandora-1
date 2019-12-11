import os
import time
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .validators import validate_file_extension


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "src.%s" % (ext)
    return os.path.join('submitions/', '%s/' % instance.contest.short_name, 'user_%s/' % instance.user.id,
                        'submition_%s/' % time.strftime("%Y%m%d%H%M%S"), filename)


def get_tests_path(instance, filename):
    print("*************************************************************************************")
    print(filename)
    print("*************************************************************************************")
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('contests/%s' % instance.contest.short_name, 'tests/', filename)


def get_contest_detail_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "sow.%s" % (ext)
    return os.path.join('contests/%s' % instance.short_name, filename)


def get_contest_code_path(instance, filename):
    return os.path.join('contests/%s' % instance.short_name, 'src/', filename)


def get_contest_ins_files_path(instance, filename):
    return os.path.join('contests/%s' % instance.short_name, 'src/temp/in', filename)


def get_contest_outs_files_path(instance, filename):
    return os.path.join('contests/%s' % instance.short_name, 'src/temp/out', filename)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    number = models.IntegerField(null=True, blank=True)
    gprd = models.BooleanField(null=True, default=True, blank=True)
    valid = models.BooleanField(null=False, default=False, blank=False)

    def __str__(self):  # __unicode__ for Python 2
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class Contest(models.Model):
    print(str(get_contest_code_path) + '/temp')
    title = models.CharField(max_length=128)
    short_name = models.CharField(max_length=16, blank=False, unique=True)
    description = models.TextField(null=True, blank=True)
    sow = models.FileField(upload_to=get_contest_detail_path, blank=True, null=True, max_length=512)

    # in_files = models.FileField(upload_to=get_contest_ins_files_path, blank=True, null=True)
    reference_code = models.FileField(upload_to=get_contest_code_path, blank=True, null=True)
    # out_files = models.FileField(upload_to=get_contest_outs_files_path, blank=True, null=True)

    start_date = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    end_date = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, blank=True)
    min_team_members = models.PositiveSmallIntegerField(default=1)
    max_team_members = models.PositiveSmallIntegerField(default=3)
    compile_flags = models.CharField(max_length=120)
    linkage_flags = models.CharField(max_length=120)
    max_classification = models.IntegerField(default=20)
    visible = models.BooleanField(null=False, default=True, blank=False)
    automatic_weight = models.BooleanField(null=False, default=True, blank=False)
    max_submitions = models.PositiveIntegerField(default=0)
    # safexec options
    cpu = models.PositiveIntegerField(default=1)  # <seconds>		Default: 1 second(s)
    mem = models.PositiveIntegerField(default=32768)  # <kbytes>		Default: 32768 kbyte(s)
    space = models.PositiveIntegerField(default=0)  # <kbytes>		Default: 0 kbyte(s)
    minuid = models.PositiveIntegerField(default=5000)  # <uid>			Default: 5000
    maxuid = models.PositiveIntegerField(default=65535)  # <uid>			Default: 65535
    core = models.PositiveIntegerField(default=0)  # <kbytes>		Default: 0 kbyte(s)
    nproc = models.PositiveIntegerField(default=0)  # <number>		Default: 0 proccess(es)
    fsize = models.PositiveIntegerField(default=8192)  # <kbytes>		Default: 8192 kbyte(s)
    stack = models.PositiveIntegerField(default=8192)  # <kbytes>		Default: 8192 kbyte(s)
    clock = models.PositiveIntegerField(default=10)  # <seconds>		Wall clock timeout (default: 10)
    chroot = models.CharField(default='/tmp', max_length=128)  # <path>		Directory to chrooted (default: /tmp)

    def is_open(self):
        "Returns true if the contest is on going."
        from django.utils import timezone
        if timezone.now() < self.end_date and timezone.now() > self.start_date:
            return True
        return False

        # objects = ContestManager()

    def get_absolute_url(self):
        return "/contests/%i/" % self.id
        # return f"/contests/{self.id}/"


class Test(models.Model):
    contest = models.ForeignKey(Contest, default=1, null=False, on_delete=models.CASCADE)
    input_file = models.FileField(upload_to=get_tests_path, blank=False, null=False, max_length=512)
    output_file = models.FileField(upload_to=get_tests_path, blank=False, null=False, max_length=512)
    mandatory = models.BooleanField(null=False, default=False)
    weight_pct = models.DecimalField(default=10, null=False, decimal_places=2, max_digits=6)
    run_arguments = models.CharField(max_length=512, null=True, blank=True)
    use_for_time_benchmark = models.BooleanField(null=False, default=False)
    use_for_memory_benchmark = models.BooleanField(null=False, default=False)
    type_of_feedback = models.PositiveIntegerField(default=1, null=False, blank=False)
    # test specific options
    override_exec_options = models.BooleanField(null=False, default=False)
    cpu = models.PositiveIntegerField(default=1)  # <seconds>           Default: 1 second(s)
    mem = models.PositiveIntegerField(default=32768)  # <kbytes>            Default: 32768 kbyte(s)
    space = models.PositiveIntegerField(default=0)  # <kbytes>            Default: 0 kbyte(s)
    core = models.PositiveIntegerField(default=0)  # <kbytes>            Default: 0 kbyte(s)
    nproc = models.PositiveIntegerField(default=0)  # <number>            Default: 0 proccess(es)
    fsize = models.PositiveIntegerField(default=8192)  # <kbytes>            Default: 8192 kbyte(s)
    stack = models.PositiveIntegerField(default=8192)  # <kbytes>            Default: 8192 kbyte(s)
    clock = models.PositiveIntegerField(default=10)  # <seconds>           Wall clock timeout (default: 10)


class Team(models.Model):
    name = models.CharField(max_length=16, blank=True)
    contest = models.ForeignKey(Contest, default=1, null=False, on_delete=models.CASCADE)

    # image  = models.ImageField(upload_to='images/', blank=True, null=True)

    def _get_active(self):
        "Returns True if the team is active"
        n_members = self.teammember_set.filter(approved=True).count()
        return n_members >= self.contest.min_team_members and n_members <= self.contest.max_team_members

    active = property(_get_active)

    class Meta:
        unique_together = ('name', 'contest')

    def get_absolute_url(self):
        return f"/teams/{self.id}/"


class Atempt(models.Model):
    contest = models.ForeignKey(Contest, default=1, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=1, null=False, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, default=1, null=True,
                             on_delete=models.SET_NULL)  # this is redundant but it's just easier...
    date = models.DateTimeField(auto_now_add=True, blank=True)
    file = models.FileField(upload_to=get_file_path, blank=False, null=False, max_length=512,
                            validators=[validate_file_extension])

    comment = models.CharField(null=True, max_length=128, blank=True)
    compile_error = models.BooleanField(null=False, default=False, blank=True)
    failed_mandatory_test = models.BooleanField(null=False, default=False, blank=True)
    error_description = models.TextField(null=True, blank=True)
    grade = models.IntegerField(blank=True, null=True, default=0)
    time_benchmark = models.IntegerField(blank=True, null=True, default=0)
    memory_benchmark = models.IntegerField(blank=True, null=True, default=0)
    elapsed_time = models.IntegerField(blank=True, null=True, default=0)
    cpu_time = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=8)

    def get_absolute_url(self):
        return "/contests/atempt/%i/" % self.id


class SafeExecError(models.Model):
    description = models.CharField(null=False, max_length=128, unique=True, blank=False)


class Classification(models.Model):
    attempt = models.ForeignKey(Atempt, default=1, null=False, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, default=1, null=False, on_delete=models.CASCADE)
    passed = models.BooleanField(null=False, default=False)
    output = models.FileField(blank=True, null=True, max_length=512)
    report_file = models.FileField(blank=True, null=True, max_length=512)
    execution_time = models.IntegerField(blank=True, null=True)
    error_description = models.TextField(null=True, blank=True)
    error = models.ForeignKey(SafeExecError, blank=True, null=True, on_delete=models.SET_NULL)
    memory_usage = models.IntegerField(blank=True, null=True)
    cpu_time = models.DecimalField(blank=True, null=True, decimal_places=3, max_digits=8)
    elapsed_time = models.IntegerField(blank=True, null=True)
    exception = models.TextField(null=True, blank=True)


class TeamMember(models.Model):
    team = models.ForeignKey(Team, default=1, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey(User, default=1, null=False, on_delete=models.CASCADE)
    approved = models.BooleanField(null=False, default=False, blank=True)
    unique_together = ('team', 'user')

# class TeamManager(models.Manager):
#	use_for_related_fields = True

#	def number_of_elements(self, user, team):
#		Full_team_obj = TeamMember.objects.all().select_related('team').filter(team__contest = contest_obj.id).first()
