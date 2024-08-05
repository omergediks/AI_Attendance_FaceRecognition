import { Injectable } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

@Injectable({
  providedIn: 'root'
})
export class PhotoService {

  constructor() { }

  async takePicture(): Promise<string | null> {
    try {
      const image = await Camera.getPhoto({
        quality: 100,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera
      });

      // `image.dataUrl`'ın `undefined` olup olmadığını kontrol edin
      return image.dataUrl || null; // `undefined` ise `null` döner
    } catch (err) {
      console.error(err);
      return null; // Hata durumunda `null` döner
    }
  }
}
