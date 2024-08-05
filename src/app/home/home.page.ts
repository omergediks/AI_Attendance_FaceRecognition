import { Component } from '@angular/core';
import { PhotoService } from '../services/photo.service';
import { ApiService } from '../services/api.service';
import { ToastController } from '@ionic/angular';

// Define interfaces for the API response
interface RecognizedFace {
  name: string;
  confidence: number;
  box: [number, number, number, number];  // [top, right, bottom, left]
  photoDataUrl: string;  // Add this line
}

interface AttendanceResponse {
  recognized_faces: RecognizedFace[];
  image_base64: string;  // Base64 encoded processed image
}

@Component({
  selector: 'app-home',
  templateUrl: 'home.page.html',
  styleUrls: ['home.page.scss'],
})
export class HomePage {
  firstName: string = '';
  lastName: string = '';
  recognizedFaces: RecognizedFace[] = [];  // List of recognized faces
  processedImageDataUrl: string = '';  // Base64 data URL of the processed image

  constructor(
    private photoService: PhotoService,
    private apiService: ApiService,
    private toastController: ToastController
  ) {}

  // Function to add a person
  async addPerson() {
    try {
      const imageData = await this.photoService.takePicture();
      if (imageData) {
        this.apiService.uploadImage(imageData, this.firstName, this.lastName).subscribe(
          async response => {
            console.log('Image uploaded successfully:', response);
            await this.showToast('Person added successfully');
          },
          error => {
            console.error('Error uploading image:', error);
            this.showToast('Error uploading image');
          }
        );
      }
    } catch (error) {
      console.error('Error taking picture:', error);
      this.showToast('Error taking picture');
    }
  }

  // Function to check attendance
  async checkAttendance() {
    try {
      const imageData = await this.photoService.takePicture();
      if (imageData) {
        this.apiService.checkAttendance(imageData).subscribe(
          response => {
            console.log('Attendance checked:', response);
            // Map the response to include photoDataUrl
            this.recognizedFaces = response.recognized_faces.map((face: { name: any; confidence: any; box: any; photoDataUrl: any; }) => ({
              name: face.name,
              confidence: face.confidence,
              box: face.box,
              photoDataUrl: `${face.photoDataUrl}` // Ensure the format is correct
            }));
            this.processedImageDataUrl = `${response.image_base64}`;
          },
          error => {
            console.error('Error checking attendance:', error);
            this.showToast('Error checking attendance');
          }
        );
      }
    } catch (error) {
      console.error('Error taking picture:', error);
      this.showToast('Error taking picture');
    }
  }

  async showToast(message: string) {
    const toast = await this.toastController.create({
      message: message,
      duration: 2000,
      position: 'bottom',
      color: 'success',
    });
    toast.present();
  }
}
