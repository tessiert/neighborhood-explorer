from django.shortcuts import render
from django.views.generic import View

from api.models import Searches


# Create your views here.
class HomeView(View):
    NUM_TOP_SEARCHES = 5

    def get(self, request):
        new_search = Searches()
        top_searches = new_search.__class__.objects.order_by("-count")[: self.NUM_TOP_SEARCHES]
        return render(request, template_name="pages/home.html", context={"top_searches": top_searches})

NUM_TOP_SEARCHES = 5    
 # Use function-based view here so that home page updates top searches list
 # with each visit   
def home_view(request):
        top_searches = Searches.objects.order_by("-count")[: NUM_TOP_SEARCHES]
        return render(request, template_name="pages/home.html", context={"top_searches": top_searches})    
