from django.db import models
from users.models import User

DEPARTMENT_COURSES = {
    'engineering': [
        'Python','Java','JavaScript','React JS','Node JS',
        'Django','REST API','HTML','CSS','SQL',
        'Git & GitHub','Linux','Docker','Kubernetes',
        'AWS','DevOps','System Design',
    ],
    'hr': [
        'Recruitment Process','Employee Onboarding','Payroll Management',
        'Performance Management','Labor Laws','Conflict Resolution',
        'Communication Skills','MS Excel','HR Analytics',
    ],
    'finance': [
        'Accounting Basics','GST','Tally','Financial Reporting',
        'Taxation','Advanced Excel','Budget Planning','SAP Finance','Power BI',
    ],
    'operations': [
        'Manual Testing','Automation Testing','Selenium','Java for Testing',
        'Python for Testing','API Testing','Postman','JMeter',
        'TestNG','SQL Testing','Bug Tracking (JIRA)','Agile Methodology',
    ],
    'marketing': [
        'Digital Marketing','SEO','SEM','Google Ads','Meta Ads',
        'Content Marketing','Email Marketing','Canva','Analytics',
        'Social Media Marketing',
    ],
    'design': [
        'UI Design','UX Design','Figma','Adobe XD','Photoshop',
        'Illustrator','Design Systems','Wireframing','Prototyping',
    ],
    'sales': [
        'Sales Fundamentals','Lead Generation','CRM Tools',
        'Negotiation Skills','Customer Communication',
        'B2B Sales','B2C Sales','Sales Analytics',
    ],
}

DIFFICULTY = [('beginner','Beginner'),('intermediate','Intermediate'),('advanced','Advanced')]


class Course(models.Model):
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    department   = models.CharField(max_length=50)
    difficulty   = models.CharField(max_length=20, choices=DIFFICULTY, default='beginner')
    duration_hrs = models.IntegerField(default=5)
    thumbnail    = models.CharField(max_length=10, default='📚')  # emoji
    lessons      = models.JSONField(default=list)   # list of lesson titles
    quiz         = models.JSONField(default=list)   # list of {question, options, answer}
    pass_score   = models.IntegerField(default=70)  # percentage to pass
    created_by   = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, related_name='created_courses')
    created_at   = models.DateTimeField(auto_now_add=True)
    is_active    = models.BooleanField(default=True)

    class Meta:
        db_table = 'courses'

    def __str__(self):
        return f"{self.title} ({self.department})"


class CourseEnrollment(models.Model):
    STATUS = [
        ('enrolled',   'Enrolled'),
        ('in_progress','In Progress'),
        ('completed',  'Completed'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE,
                                        related_name='enrollments')
    course          = models.ForeignKey(Course, on_delete=models.CASCADE,
                                        related_name='enrollments')
    status          = models.CharField(max_length=20, choices=STATUS, default='enrolled')
    progress        = models.IntegerField(default=0)        # 0-100%
    lessons_done    = models.JSONField(default=list)        # list of completed lesson indices
    quiz_score      = models.IntegerField(null=True, blank=True)
    quiz_passed     = models.BooleanField(default=False)
    enrolled_at     = models.DateTimeField(auto_now_add=True)
    completed_at    = models.DateTimeField(null=True, blank=True)
    certificate_id  = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table        = 'course_enrollments'
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.full_name} → {self.course.title}"