from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api import models as api_models

# Define a custom serializer that inherits from TokenObtainPairSerializer
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''
    class MyTokenObtainPairSerializer(TokenObtainPairSerializer):: This line creates a new token serializer called MyTokenObtainPairSerializer that is based on an existing one called TokenObtainPairSerializer. Think of it as customizing the way tokens work.
    @classmethod: This line indicates that the following function is a class method, which means it belongs to the class itself and not to an instance (object) of the class.
    def get_token(cls, user):: This is a function (or method) that gets called when we want to create a token for a user. The user is the person who's trying to access something on the website.
    token = super().get_token(user): Here, it's asking for a regular token from the original token serializer (the one it's based on). This regular token is like a key to enter the website.
    token['full_name'] = user.full_name, token['email'] = user.email, token['username'] = user.username: This code is customizing the token by adding extra information to it. For example, it's putting the user's full name, email, and username into the token. These are like special notes attached to the key.
    return token: Finally, the customized token is given back to the user. Now, when this token is used, it not only lets the user in but also carries their full name, email, and username as extra information, which the website can use as needed.
    '''
    @classmethod
    # Define a custom method to get the token for a user
    def get_token(cls, user):
        # Call the parent class's get_token method
        token = super().get_token(user)

        # Add custom claims to the token
        token['full_name'] = user.full_name
        token['email'] = user.email
        token['username'] = user.username
        # try:
        #     token['vendor_id'] = user.vendor.id
        # except:
        #     token['vendor_id'] = 0

        # ...

        # Return the token with custom claims
        return token

# Define a serializer for user registration, which inherits from serializers.ModelSerializer
class RegisterSerializer(serializers.ModelSerializer):
    # Define fields for the serializer, including password and password2
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        # Specify the model that this serializer is associated with
        model = api_models.User
        # Define the fields from the model that should be included in the serializer
        fields = ('full_name', 'email',  'password', 'password2')

    def validate(self, attrs):
        # Define a validation method to check if the passwords match
        if attrs['password'] != attrs['password2']:
            # Raise a validation error if the passwords don't match
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Return the validated attributes
        return attrs

    def create(self, validated_data):
        # Define a method to create a new user based on validated data
        user = api_models.User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
        )
        email_username, mobile = user.email.split('@')
        user.username = email_username

        # Set the user's password based on the validated data
        user.set_password(validated_data['password'])
        user.save()

        # Return the created user
        return user

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = api_models.User
        fields = '__all__'

class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)


    class Meta:
        model = api_models.Profile
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
    
    def to_representation(self, instance):
        """Override to return absolute image URL on read."""
        ret = super().to_representation(instance)
        request = self.context.get('request')
        image_field = instance.image
        if image_field and hasattr(image_field, 'url'):
            url = request.build_absolute_uri(image_field.url) if request else image_field.url
            ret['image'] = url
        else:
            ret['image'] = None
        return ret

    # def to_representation(self, instance):
    #     response = super().to_representation(instance)
    #     response['user'] = UserSerializer(instance.user).data
    #     return response

# class PasswordResetSerializer(serializers.Serializer):
#     email = serializers.EmailField()



class CategorySerializer(serializers.ModelSerializer):
    # post_count = serializers.SerializerMethodField()

    '''
        category.post_set: In Django, when you define a ForeignKey relationship from one model to another 
        (e.g., Post model having a ForeignKey relationship to the Category model), 
        Django creates a reverse relationship from the related model back to the model that has the ForeignKey. 
        By default, this reverse relationship is named <model>_set. In this case, since the Post model has a 
        ForeignKey to the Category model, Django creates a reverse relationship from Category to Post named post_set. 
        This allows you to access all Post objects related to a Category instance.
    '''
    def get_post_count(self, category):
        return category.posts.count()
    
    class Meta:
        model = api_models.Category
        fields = [
            "id",
            "title",
            "image",
            "slug",
            "post_count",
        ]

    # def __init__(self, *args, **kwargs):
    #     super(CategorySerializer, self).__init__(*args, **kwargs)
    #     request = self.context.get('request')
    #     if request and request.method == 'POST':
    #         self.Meta.depth = 0
    #     else:
    #         self.Meta.depth = 3

class CommentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = api_models.Comment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CommentSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 1


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True)
    bookmark_count = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    profile = serializers.SerializerMethodField()

    
    class Meta:
        model = api_models.Post
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(PostSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3
            
    def get_bookmark_count(self, obj):
        return obj.bookmarks.count()
    
    def get_profile(self, obj):
        try:
            profile = api_models.Profile.objects.get(user=obj.user)
            request = self.context.get('request')  # grab request from context
            serializer = ProfileSerializer(profile, context={'request': request})  # pass it down
            return serializer.data
        except api_models.Profile.DoesNotExist:
            return None



class BookmarkSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = api_models.Bookmark
        fields = "__all__"


    def __init__(self, *args, **kwargs):
        super(BookmarkSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3

    
class NotificationSerializer(serializers.ModelSerializer):  

    class Meta:
        model = api_models.Notification
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(NotificationSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.method == 'POST':
            self.Meta.depth = 0
        else:
            self.Meta.depth = 3
            

class AuthorStats(serializers.Serializer):
    views = serializers.IntegerField(default=0)
    posts = serializers.IntegerField(default=0)
    likes = serializers.IntegerField(default=0)
    bookmarks = serializers.IntegerField(default=0)