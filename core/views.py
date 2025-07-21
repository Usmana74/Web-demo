from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .forms import CheckoutForm, CouponForm, RefundForm
from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon, Refund, Category
from django.http import HttpResponseRedirect
from django.db.models.functions import TruncMonth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.urls import reverse
# Create your views here.
import random
import string
import stripe
import os
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')



def landing_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')  # Namespaced redirect
    return render(request, 'landing.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def index_view(request):
    return render(request, 'index.html')  # Or your actual homepage


def about_view(request):
    return render(request, 'about.html')

from django.shortcuts import render

from django.contrib import messages
from .forms import UserUpdateForm

@login_required
def dashboard_view(request):
    user = request.user
    orders = Order.objects.filter(user=user)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('core:dashboard')
    else:
        form = UserUpdateForm(instance=user)

    return render(request, 'dashboard.html', {
        'user': user,
        'orders': orders,
        'form': form
    })

def contact_view(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            message=request.POST.get('message')
        )
        messages.success(request, "Your message has been sent successfully.")
        return redirect(reverse('core:contact'))
    return render(request, 'contact.html')



def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class PaymentView(View):
    def get(self, *args, **kwargs):
        # order
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "u have not added a billing address")
            return redirect("core:checkout")

from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from .models import Order, Payment
from django.core.exceptions import ObjectDoesNotExist

def create_ref_code():
    # Your ref code logic here
    import uuid
    return str(uuid.uuid4()).replace("-", "")[:12]

class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }
            return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                # Save billing address
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                payment_option = form.cleaned_data.get('payment_option')

                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                    address_type='B'
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()

                # Handle Payment Redirect
                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected.")
                    return redirect("core:checkout")
            else:
                messages.warning(self.request, "Please fill out the form correctly.")
                context = {
                    'form': form,
                    'couponform': CouponForm(),
                    'order': order,
                    'DISPLAY_COUPON_FORM': True
                }
                return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("core:order-summary")




class HomeView(ListView):
    template_name = "index.html"
    queryset = Item.objects.filter(is_active=True)
    context_object_name = 'items'


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")


class ShopView(ListView):
    model = Item
    paginate_by = 6
    template_name = "shop.html"


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-detail.html"


# class CategoryView(DetailView):
#     model = Category
#     template_name = "category.html"

class CategoryView(View):
    def get(self, *args, **kwargs):
        category = Category.objects.get(slug=self.kwargs['slug'])
        item = Item.objects.filter(category=category, is_active=True)
        context = {
            'object_list': item,
            'category_title': category,
            'category_description': category.description,
            'category_image': category.image
        }
        return render(self.request, "category.html", context)



# def home(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "index.html", context)
#
#
# def products(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "product-detail.html", context)
#
#
# def shop(request):
#     context = {
#         'items': Item.objects.all()
#     }
#     return render(request, "shop.html", context)


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Item qty was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Item was added to your cart.")
    return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "Item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            # add a message saying the user dosent have an order
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying the user dosent have an order
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item qty was updated.")
            return redirect("core:order-summary")
        else:
            # add a message saying the user dosent have an order
            messages.info(request, "Item was not in your cart.")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying the user dosent have an order
        messages.info(request, "u don't have an active order.")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")

            except ObjectDoesNotExist:
                messages.info(request, "You do not have an active order")
                return redirect("core:checkout")


class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            # edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                # store the refund
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request was received")
                return redirect("core:request-refund")

            except ObjectDoesNotExist:
                messages.info(self.request, "This order does not exist")
                return redirect("core:request-refund")

from django.shortcuts import redirect
from django.contrib import messages

def admin_redirect(request):
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.role == 'admin':
            return redirect('/admin/')  # or use reverse()
        else:
            messages.error(request, "Access denied: You do not have admin privileges.")
            return redirect('core:dashboard')
    else:
        messages.error(request, "Please log in with an admin account to access this area.")
        return redirect('core:login')

from django.http import JsonResponse
from django.contrib.auth.models import User
from core.models import Order  # Adjust if your model is named differently

def chart_data(request):
    total_users = User.objects.count()
    total_orders = Order.objects.count()  # Adjust based on your actual model
    data = {
        'labels': ['Users', 'Orders'],
        'data': [total_users, total_orders],
    }
    return JsonResponse(data)

from django.contrib.auth.decorators import user_passes_test

def is_admin(user):
    return user.is_authenticated and user.profile.role == 'admin'


from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth
from django.db.models import Count
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from .models import Order, User  # adjust models as per your project
from django.db.models import Count
from django.db.models.functions import TruncMonth

@login_required
def admin_dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    orders = Order.objects.all()
    users = User.objects.all()

    monthly_orders = (
        orders
        .annotate(month=TruncMonth("ordered_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    context = {
        "orders": orders,
        "users": users,
        "monthly_orders": monthly_orders,
    }

    return render(request, "admin_dashboard.html", context)

from django.http import JsonResponse

def chart_data(request):
    # Sample dummy data — replace with real logic if needed
    data = {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
        "data": [120, 150, 300, 200, 180]
    }
    return JsonResponse(data)

def admin_redirect(request):
    return redirect('/admin/login/?next=/admin_dashboard/')


  





