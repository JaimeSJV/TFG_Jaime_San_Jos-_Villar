from django.shortcuts import render, HttpResponse
from django.shortcuts import render, redirect
from .forms import CuadForm
from .utils import t_corr

# Create your views here.
def home(request):
    return HttpResponse("Hello world!")

def cuad_image_view(request):
    
    solutions = {}

    test_options = []

    with open("solutions.txt", "r") as file:
        for line in file:
            parts = line.strip().split(':')
            solutions[parts[0]] = parts[1]
            test_options.append({'value': parts[0], 'label': parts[0]})


    if request.method == 'POST':
        try:
            form = CuadForm(request.POST, request.FILES)
            if form.is_valid():
                print('Form is valid')
                image_file = request.FILES['Imagen_cuadricula']
                image_data = image_file.read()
                image_file.seek(0)
                test_type = request.POST.get('test_type', 'Test_A')
                sol = solutions[test_type]
                print('Test type:', test_type)
                b, m, n, t = t_corr(image_file, sol)
                return render(request, "cuadr.html", {
                    'form': form, 
                    'cor': b, 
                    'inc': m, 
                    'nota': n,
                    'selected_test': test_type,
                    'test_options': test_options,
                    'test_res': t
                })
            else: 
                return HttpResponse('Invalid form')     
        except KeyError:
            return HttpResponse('No image field in request')
        except Exception as e:
            return HttpResponse(f'Error processing image: {str(e)}')
    else:
        form = CuadForm()
    return render(request, "cuadr.html", {
        'form': form, 
        'cor': "-", 
        'inc': "-", 
        'nota': "-",
        'selected_test': 'Test_A',
        'test_options': test_options,
        'test_res': "-"})