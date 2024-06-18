from io import BytesIO
import requests
from urllib.parse import urljoin
from settings import DEEPAI_API_KEY, S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from enum import Enum
import boto3
import uuid


class S3Bucket:
    def __init__(self):
        self.bucket_name = S3_BUCKET
        self.aws_access_key_id = AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        self.aws_region = AWS_REGION

    def download_image(self, url):
        # download image from url
        response = requests.get(url)
        return response.content

    def upload_image(self, image_bytes: bytes):
        session = boto3.session.Session()
        s3 = session.client(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

        image_name = f"Users/autogen/profile/{uuid.uuid4()}.jpg"
        s3.upload_fileobj(BytesIO(image_bytes), self.bucket_name, image_name, ExtraArgs={'ACL': 'public-read'})

        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{image_name}"

    def upload_image_from_url(self, url):
        image_bytes = self.download_image(url)
        return self.upload_image(image_bytes)


class ImageGeneratorVersionOptions(Enum):
    STANDARD = 'standard'
    HD = 'hd'
    GENIUS = 'genius'


class DeepAIClient:
    def __init__(self):
        self.api_key = DEEPAI_API_KEY
        self.base_url = "https://api.deepai.org/api/"

    @property
    def __headers(self):
        return {'api-key': self.api_key}

    def __post(self, data, endpoint):
        url = urljoin(self.base_url, endpoint)
        return requests.post(url, data=data, headers=self.__headers)

    def __get(self, endpoint, params=None):
        return requests.get(urljoin(self.base_url, endpoint), params=params, headers=self.__headers)

    def generate_image(self, prompt, image_generator_version='hd'):
        """Post a text string directly to the DeepAI text2img API."""
        payload = {
            'text': prompt,
            'image_generator_version': image_generator_version,
            'grid_size': '1',
        }

        response = self.__post(payload, 'text2img')
        return response.json()


if __name__ == "__main__":
    client = DeepAIClient()

    prompt = """Deborah Huffman's 43yo profile picture for travel application:
    I'm Deborah Huffman, a dedicated statistician with a passion for numbers and analysis. In my free time, I enjoy exploring the city, trying out new restaurants, and attending live music events. I also love to stay active by hiking and practicing yoga. My work keeps me busy, but I always make time for my hobbies and interests."""

    response = client.generate_image(prompt)
    print(response)

    s3 = S3Bucket()

    url = response['output_url']

    print(s3.upload_image_from_url(url))
