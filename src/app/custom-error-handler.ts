import { ErrorHandler } from '@angular/core';

export class CustomErrorHandler implements ErrorHandler {
  handleError(error) {
    // Do what you want here, but throw it so that it's visible on the console!
    throw new Error(error);
  }
}
