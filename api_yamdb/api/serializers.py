from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.shortcuts import get_object_or_404
from api.service import send_code_to_email, get_tokens_for_user
import datetime as dt
from reviews.models import Review, Comment
from titles.models import Category, Genre, Title
from user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['username', 'email', 'first_name',
                  'last_name', 'bio', 'role']
        model = User

    def validate(self, data):
        role = self.context.get('role')
        if 'role' in data and role == 'user':
            raise serializers.ValidationError(
                "User не может изменить свою роль")
        return data


class UserMeSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)


class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['username', 'email']
        model = User

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            confirmation_code=self.context["code"]
        )
        user.save()
        send_code_to_email(self.context["code"], validated_data['email'])
        return user

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError(
                "Имя 'me' нельзя использовать")
        return data


class TokenSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        username = data.get('username')
        confirmation_code = data.get('confirmation_code')

        if username is None or confirmation_code is None:
            raise serializers.ValidationError(
                {"o-ops": "Забыли указать данные"}
            )

        user = get_object_or_404(User, username=username)

        if user.confirmation_code == int(confirmation_code):
            token = get_tokens_for_user(user)
        else:
            raise serializers.ValidationError(
                {"o-ops": "Неправильный проверочный код"}
            )

        return {
            'token_refresh': token['refresh'],
            'token_access': token['access']
        }

    def to_representation(self, instance):
        return {
            'refresh': instance['token_refresh'],
            'access': instance['token_access']
        }


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        exclude = ('id',)


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        exclude = ('id',)


class WriteTitleSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(), slug_field='slug', many=True
    )
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(), slug_field='slug'
    )
    year = serializers.IntegerField()

    def validate_year(self, value):
        year = dt.date.today().year
        if not (0 < value <= year):
            raise serializers.ValidationError(
                'Год выпуска не может быть больше текущего!'
            )
        return value

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'description', 'genre', 'category')


class ReadTitleSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField()
    name = serializers.CharField()
    genre = GenreSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Title
        fields = ('id', 'name', 'year', 'rating', 'description',
                  'genre', 'category',)


class CurrentTitleDefault:
    requires_context = True

    def __call__(self, serializer_field):
        return serializer_field.context['view'].kwargs.get('titles_id')

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',
        default=serializers.CurrentUserDefault(),
    )
    title = serializers.HiddenField(default=CurrentTitleDefault(),)

    class Meta:
        fields = '__all__'
        model = Review
        validators = [
            UniqueTogetherValidator(
                queryset=Review.objects.all(),
                fields=('author', 'title'),
                message='Не более одного комментария для произведения'
            )
        ]

    def validate_score(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError('Поставьте оценку от 1 до 10')
        return value


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username',)

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment
