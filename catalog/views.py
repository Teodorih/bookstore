import datetime

from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from .forms import RenewBookForm, DocumentForm, FileUploadForm
from .models import Book, Author, BookInstance, Genre, Document, User
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from catalog.tasks import upload_file, make_thumbnails

import os
from celery import current_app
from django import forms
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View


def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # Метод 'all()' применён по умолчанию.

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'index.html',
        context={'num_books':num_books,'num_instances':num_instances,'num_instances_available':num_instances_available,'num_authors':num_authors,
                 'num_visits': num_visits},
    )


class BookListView(generic.ListView):
    model = Book
    paginate_by = 5
    context_object_name = 'book_list'  # ваше собственное имя переменной контекста в шаблоне

    def get_context_data(self, **kwargs):
        # В первую очередь получаем базовую реализацию контекста
        context = super(BookListView, self).get_context_data(**kwargs)
        # Добавляем новую переменную к контексту и инициализируем её некоторым значением
        context['some_data'] = 'This is just some data'
        return context


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10
    context_object_name = 'author_list'  # ваше собственное имя переменной контекста в шаблоне


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class BookOnLoanView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/books_onloan.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst = get_object_or_404(BookInstance, pk=pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('on-loan-books') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']


class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')


class BookCreate(CreateView):
    model = Book
    fields = '__all__'


class BookUpdate(UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']


class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')


def files(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            path = request.FILES['docfile'].temporary_file_path()
            upload_file.delay(path, request.FILES['docfile'].name)
            return HttpResponseRedirect(reverse('files'))
    else:
        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    documents = Document.objects.all()

    # Render list page with the documents and the form
    return render(
        request,
        'catalog/files.html',
        {'documents': documents, 'form': form}
    )


def verify(request, uuid):
    try:
        user = User.objects.get(verification_uuid=uuid, is_verified=False)
    except User.DoesNotExist:
        raise Http404("User does not exist or is already verified")

    user.is_verified = True
    user.save()

    return redirect('index')


class HomeView(View):
    def get(self, request):
        form = FileUploadForm()
        return render(request, 'thumbnailer/home.html', { 'form': form })

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        context = {}
        if form.is_valid():
            file_path = os.path.join(settings.IMAGES_DIR, request.FILES['image_file'].name)
            with open(file_path, 'wb+') as fp:
                for chunk in request.FILES['image_file']:
                    fp.write(chunk)
            task = make_thumbnails.delay(file_path, thumbnails=[(128, 128)])
            context['task_id'] = task.id
            context['task_status'] = task.status
            return render(request, 'thumbnailer/home.html', context)
        context['form'] = form
        return render(request, 'thumbnailer/home.html', context)


class TaskView(View):
    def get(self, request, task_id):
        task = current_app.AsyncResult(task_id)
        response_data = {'task_status': task.status, 'task_id': task.id}
        if task.status == 'SUCCESS':
            response_data['results'] = task.get()
        return JsonResponse(response_data)