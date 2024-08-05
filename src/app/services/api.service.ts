import { Injectable } from '@angular/core';
import { HttpClient,HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = 'http://127.0.0.1:5000'; // Replace with your IP address

  constructor(private http: HttpClient) { }

  uploadImage(imageData: string, firstName: string, lastName: string): Observable<any> {
    const body = { firstName, lastName, photo: imageData }; // Ensure the keys match what the Flask endpoint expects
    return this.http.post(`${this.apiUrl}/add_person`, body);
  }

  checkAttendance(imageData: string): Observable<any> {
    const body = { image: imageData }; // Ensure this matches the Flask endpoint
    return this.http.post(`${this.apiUrl}/recognize_faces`, body, {
      headers: new HttpHeaders({
        'Content-Type': 'application/json'
      })
    });
  }
  
  // Convert base64 string to Blob
  b64toBlob(b64Data: string, contentType: string = '', sliceSize: number = 512): Blob {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];
  
    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
      const slice = byteCharacters.slice(offset, offset + sliceSize);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
  
    return new Blob(byteArrays, { type: contentType });
  }
  
}
