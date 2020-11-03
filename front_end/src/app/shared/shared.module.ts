import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';


// Animation
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
// Material
import {
  MatButtonModule,
  MatCheckboxModule,
  MatCardModule,
  MatListModule,
  MatIconModule,
  MatTabsModule,
  MatTooltipModule,
  MatGridListModule,
  MatProgressBarModule,
  MatSelectModule,
  MatSnackBarModule,
  MatExpansionModule,
  MatBadgeModule,
  MatSlideToggleModule,
  MatTableModule,
  MatInputModule,
  MatPaginatorModule,
  MatSortModule,
  MatChipsModule
} from '@angular/material';
import {MatBottomSheetModule} from '@angular/material/bottom-sheet';

import { LoaderComponent } from './loader/loader.component';

@NgModule({
  imports: [
    CommonModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatCheckboxModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatTabsModule,
    MatTooltipModule,
    MatGridListModule,
    MatProgressBarModule,
    MatSelectModule,
    MatSnackBarModule,
    MatExpansionModule,
    MatBadgeModule,
    MatSlideToggleModule,
    MatTableModule,
    MatInputModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatBottomSheetModule
  ],
  declarations: [LoaderComponent],
  exports: [
    CommonModule,
    BrowserAnimationsModule,
    MatButtonModule,
    MatCheckboxModule,
    MatCardModule,
    MatListModule,
    MatIconModule,
    MatTabsModule,
    MatTooltipModule,
    MatGridListModule,
    MatProgressBarModule,
    MatSelectModule,
    MatSnackBarModule,
    MatExpansionModule,
    MatBadgeModule,
    LoaderComponent,
    MatSlideToggleModule,
    MatTableModule,
    MatInputModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule,
    MatBottomSheetModule
  ]
})
export class SharedModule { }
