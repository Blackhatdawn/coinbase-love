/**
 * KYC Page - Identity Verification
 * Professional multi-step verification process
 */
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  User,
  MapPin,
  FileText,
  Camera,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ChevronLeft,
  Upload,
  Loader2,
  Shield,
  Clock,
  Briefcase,
  TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { api } from '@/lib/apiClient';
import { cn } from '@/lib/utils';
import DashboardCard from '@/components/dashboard/DashboardCard';
import axios from 'axios';

const STEPS = [
  { id: 'personal', title: 'Personal Info', icon: User },
  { id: 'address', title: 'Address', icon: MapPin },
  { id: 'document', title: 'ID Document', icon: FileText },
  { id: 'selfie', title: 'Selfie', icon: Camera },
];

const ID_TYPES = [
  { value: 'passport', label: 'Passport' },
  { value: 'national_id', label: 'National ID' },
  { value: 'drivers_license', label: 'Driver\'s License' },
];

const KYC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    fullName: '',
    dateOfBirth: '',
    phoneNumber: '',
    occupation: '',
    country: '',
    city: '',
    address: '',
    postalCode: '',
    idType: 'passport',
  });

  // Files State
  const [files, setFiles] = useState<{
    idFront: File | null;
    idBack: File | null;
    addressProof: File | null;
    selfie: File | null;
  }>({
    idFront: null,
    idBack: null,
    addressProof: null,
    selfie: null,
  });

  // S3 Keys State
  const [keys, setKeys] = useState<{
    idFront: string;
    idBack: string;
    addressProof: string;
    selfie: string;
  }>({
    idFront: '',
    idBack: '',
    addressProof: '',
    selfie: '',
  });

  // Fetch current KYC status
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: ['kycStatus'],
    queryFn: () => api.kyc.getStatus(),
  });

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleFileChange = (type: keyof typeof files, file: File | null) => {
    if (file && file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }
    setFiles(prev => ({ ...prev, [type]: file }));
  };

  const uploadToS3 = async (file: File, documentType: "id_front" | "id_back" | "address_proof" | "selfie") => {
    try {
      // 1. Get pre-signed URL from backend
      const { url, fields, key, mock } = await api.kyc.getPresignedUrl({
        file_name: file.name,
        content_type: file.type,
        document_type: documentType,
      });

      if (mock) {
        // Local dev mode without S3
        const formData = new FormData();
        Object.entries(fields).forEach(([k, v]) => formData.append(k, v));
        formData.append('file', file);
        await axios.post(url, formData);
        return key;
      }

      // 2. Upload directly to S3
      const s3FormData = new FormData();
      Object.entries(fields).forEach(([k, v]) => s3FormData.append(k, v));
      s3FormData.append('file', file);

      await axios.post(url, s3FormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      return key;
    } catch (error: any) {
      console.error(`Upload failed for ${documentType}:`, error);
      throw new Error(`Failed to upload ${documentType.replace('_', ' ')}`);
    }
  };

  const handleNext = () => {
    // Basic validation for each step
    if (currentStep === 0) {
      if (!formData.fullName || !formData.dateOfBirth || !formData.phoneNumber || !formData.occupation) {
        toast.error('Please fill in all personal details');
        return;
      }

      // Age validation (>= 20)
      const dob = new Date(formData.dateOfBirth);
      const now = new Date();
      let age = now.getFullYear() - dob.getFullYear();
      const m = now.getMonth() - dob.getMonth();
      if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) {
        age--;
      }

      if (age < 20) {
        toast.error('You must be at least 20 years old to complete identity verification.');
        return;
      }
    } else if (currentStep === 1) {
      if (!formData.country || !formData.city || !formData.address || !formData.postalCode) {
        toast.error('Please fill in all address details');
        return;
      }
    } else if (currentStep === 2) {
      if (!files.idFront || !files.addressProof) {
        toast.error('Please upload required documents');
        return;
      }
    }

    if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    if (!files.selfie) {
      toast.error('Please upload a verification selfie');
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading('Uploading documents and submitting application...');

    try {
      // 1. Upload all files to S3 and get keys
      const uploadPromises = [
        uploadToS3(files.idFront!, 'id_front'),
        uploadToS3(files.addressProof!, 'address_proof'),
        uploadToS3(files.selfie!, 'selfie'),
      ];

      if (files.idBack) {
        uploadPromises.push(uploadToS3(files.idBack, 'id_back'));
      }

      const results = await Promise.all(uploadPromises);

      const submissionData = {
        full_name: formData.fullName,
        date_of_birth: formData.dateOfBirth,
        phone_number: formData.phoneNumber,
        occupation: formData.occupation,
        country: formData.country,
        city: formData.city,
        address: formData.address,
        postal_code: formData.postalCode,
        id_type: formData.idType,
        id_front_key: results[0],
        proof_of_address_key: results[1],
        selfie_key: results[2],
        id_back_key: results[3] || undefined,
      };

      // 2. Submit metadata to backend
      await api.kyc.submit(submissionData);

      toast.success('KYC application submitted successfully!', { id: toastId });
      queryClient.invalidateQueries({ queryKey: ['kycStatus'] });
      // Navigation will be handled by the status display
    } catch (error: any) {
      toast.error(error.message || 'Submission failed. Please try again.', { id: toastId });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-gold-400 animate-spin" />
      </div>
    );
  }

  // If already submitted or approved
  if (statusData?.kyc_status && statusData.kyc_status !== 'unverified' && statusData.kyc_status !== 'rejected') {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <DashboardCard glowColor={statusData.kyc_status === 'approved' ? 'emerald' : 'gold'}>
          <div className="text-center space-y-6 py-8">
            <div className={cn(
              "mx-auto w-20 h-20 rounded-full flex items-center justify-center",
              statusData.kyc_status === 'approved' ? "bg-emerald-500/10" : "bg-gold-500/10"
            )}>
              {statusData.kyc_status === 'approved' ? (
                <CheckCircle2 className="h-10 w-10 text-emerald-400" />
              ) : (
                <Clock className="h-10 w-10 text-gold-400" />
              )}
            </div>

            <div>
              <h2 className="text-2xl font-display font-bold text-white">
                {statusData.kyc_status === 'approved' ? 'Identity Verified' : 'Application Pending'}
              </h2>
              <p className="text-gray-400 mt-2 max-w-md mx-auto">
                {statusData.kyc_status === 'approved'
                  ? 'Your identity has been successfully verified. You now have full access to all platform features.'
                  : 'We have received your KYC application and our compliance team is reviewing it. This typically takes less than 24 hours.'}
              </p>
            </div>

            <div className="pt-6 border-t border-white/5">
              <Button
                onClick={() => navigate('/dashboard')}
                className="bg-gold-500 hover:bg-gold-400 text-black px-8"
              >
                Go to Dashboard
              </Button>
            </div>
          </div>
        </DashboardCard>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-display font-bold text-white flex items-center gap-3">
            <Shield className="h-7 w-7 text-gold-400" />
            Identity Verification
          </h1>
          <p className="text-gray-400 mt-1">Complete KYC to unlock full trading limits</p>
        </div>

        {statusData?.kyc_status === 'rejected' && (
          <div className="flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            <AlertTriangle className="h-4 w-4" />
            <span>Previous application rejected: {statusData.rejection_reason}</span>
          </div>
        )}
      </div>

      {/* Progress Steps */}
      <div className="hidden sm:flex items-center justify-between px-4 mb-8">
        {STEPS.map((step, index) => (
          <div key={step.id} className="flex items-center group">
            <div className={cn(
              "flex flex-col items-center gap-2 transition-colors",
              index <= currentStep ? "text-gold-400" : "text-gray-500"
            )}>
              <div className={cn(
                "w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all",
                index < currentStep ? "bg-gold-500 border-gold-500 text-black" :
                index === currentStep ? "border-gold-500 text-gold-500 shadow-[0_0_15px_rgba(197,160,73,0.3)]" :
                "border-gray-700 text-gray-500"
              )}>
                {index < currentStep ? <CheckCircle2 className="h-6 w-6" /> : <step.icon className="h-5 w-5" />}
              </div>
              <span className="text-xs font-medium uppercase tracking-wider">{step.title}</span>
            </div>
            {index < STEPS.length - 1 && (
              <div className={cn(
                "w-16 h-0.5 mx-4 rounded-full",
                index < currentStep ? "bg-gold-500" : "bg-gray-800"
              )} />
            )}
          </div>
        ))}
      </div>

      {/* Form Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <DashboardCard>
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="space-y-6 py-2"
              >
                {/* Step 1: Personal Details */}
                {currentStep === 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <User className="h-5 w-5 text-gold-400" />
                      Personal Information
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Full Legal Name</Label>
                        <Input
                          placeholder="As shown on ID"
                          value={formData.fullName}
                          onChange={(e) => handleInputChange('fullName', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Date of Birth</Label>
                        <Input
                          type="date"
                          value={formData.dateOfBirth}
                          onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Phone Number</Label>
                        <Input
                          placeholder="+1 (555) 000-0000"
                          value={formData.phoneNumber}
                          onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Occupation</Label>
                        <Input
                          placeholder="e.g. Software Engineer"
                          value={formData.occupation}
                          onChange={(e) => handleInputChange('occupation', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Address Info */}
                {currentStep === 1 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-gold-400" />
                      Residential Address
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2 sm:col-span-2">
                        <Label>Street Address</Label>
                        <Input
                          placeholder="Unit, Street, etc."
                          value={formData.address}
                          onChange={(e) => handleInputChange('address', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>City</Label>
                        <Input
                          placeholder="City"
                          value={formData.city}
                          onChange={(e) => handleInputChange('city', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Postal / ZIP Code</Label>
                        <Input
                          placeholder="Code"
                          value={formData.postalCode}
                          onChange={(e) => handleInputChange('postalCode', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2 sm:col-span-2">
                        <Label>Country</Label>
                        <Input
                          placeholder="Country"
                          value={formData.country}
                          onChange={(e) => handleInputChange('country', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Document Upload */}
                {currentStep === 2 && (
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <FileText className="h-5 w-5 text-gold-400" />
                        ID Verification
                      </h3>
                      <div className="space-y-2">
                        <Label>Document Type</Label>
                        <Select value={formData.idType} onValueChange={(v) => handleInputChange('idType', v)}>
                          <SelectTrigger className="bg-white/5 border-white/10">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-[#1a1a2e] border-white/10">
                            {ID_TYPES.map(type => (
                              <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <Label className="text-gray-300">Front of ID</Label>
                        <FileUploadBox
                          file={files.idFront}
                          onFileChange={(f) => handleFileChange('idFront', f)}
                          label="Upload Front"
                        />
                      </div>
                      {formData.idType !== 'passport' && (
                        <div className="space-y-3">
                          <Label className="text-gray-300">Back of ID</Label>
                          <FileUploadBox
                            file={files.idBack}
                            onFileChange={(f) => handleFileChange('idBack', f)}
                            label="Upload Back"
                          />
                        </div>
                      )}
                      <div className="space-y-3 sm:col-span-2">
                        <Label className="text-gray-300">Proof of Address</Label>
                        <p className="text-xs text-gray-500 -mt-2">Bank statement or utility bill (last 3 months)</p>
                        <FileUploadBox
                          file={files.addressProof}
                          onFileChange={(f) => handleFileChange('addressProof', f)}
                          label="Upload Proof"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 4: Selfie Verification */}
                {currentStep === 3 && (
                  <div className="space-y-6">
                    <div className="text-center space-y-4">
                      <div className="mx-auto w-20 h-20 bg-gold-500/10 rounded-full flex items-center justify-center">
                        <Camera className="h-10 w-10 text-gold-400" />
                      </div>
                      <h3 className="text-xl font-bold text-white">Liveness Verification</h3>
                      <p className="text-gray-400 max-w-sm mx-auto">
                        Please upload a clear selfie holding your ID next to your face. Ensure all details on the ID are readable.
                      </p>
                    </div>

                    <div className="max-w-md mx-auto">
                      <FileUploadBox
                        file={files.selfie}
                        onFileChange={(f) => handleFileChange('selfie', f)}
                        label="Upload Selfie"
                        className="h-64"
                      />
                    </div>

                    <div className="bg-white/5 p-4 rounded-xl space-y-2 border border-white/5">
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-1 flex-shrink-0" />
                        <p className="text-sm text-gray-400">Face is clearly visible and centered</p>
                      </div>
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-1 flex-shrink-0" />
                        <p className="text-sm text-gray-400">ID is held clearly next to face without covering features</p>
                      </div>
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400 mt-1 flex-shrink-0" />
                        <p className="text-sm text-gray-400">Good lighting and neutral background</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Buttons */}
                <div className="flex items-center justify-between pt-6 border-t border-white/5">
                  <Button
                    variant="ghost"
                    onClick={handleBack}
                    disabled={currentStep === 0 || isSubmitting}
                    className="text-gray-400 hover:text-white"
                  >
                    <ChevronLeft className="h-4 w-4 mr-2" />
                    Back
                  </Button>

                  {currentStep < STEPS.length - 1 ? (
                    <Button
                      onClick={handleNext}
                      className="bg-gold-500 hover:bg-gold-400 text-black px-8"
                    >
                      Next Step
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  ) : (
                    <Button
                      onClick={handleSubmit}
                      disabled={isSubmitting}
                      className="bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-black font-bold px-10"
                    >
                      {isSubmitting ? (
                        <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Submitting...</>
                      ) : (
                        'Submit Verification'
                      )}
                    </Button>
                  )}
                </div>
              </motion.div>
            </AnimatePresence>
          </DashboardCard>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <DashboardCard title="Why verify?" icon={<Shield className="h-5 w-5" />}>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <div className="p-1 bg-emerald-500/10 rounded mt-0.5">
                  <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Higher Limits</p>
                  <p className="text-xs text-gray-400">Withdraw up to $100,000 daily</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="p-1 bg-emerald-500/10 rounded mt-0.5">
                  <Briefcase className="h-3.5 w-3.5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Fiat Gateway</p>
                  <p className="text-xs text-gray-400">Deposit and withdraw using bank transfers</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <div className="p-1 bg-emerald-500/10 rounded mt-0.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Full Security</p>
                  <p className="text-xs text-gray-400">Enhanced account protection and insurance</p>
                </div>
              </li>
            </ul>
          </DashboardCard>

          <DashboardCard glowColor="gold">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-gold-400 mt-1 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-white text-sm">Review Process</h4>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                  Verification usually takes 1-2 hours but may take up to 24 hours during peak times. We'll email you once it's complete.
                </p>
              </div>
            </div>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const FileUploadBox = ({
  file,
  onFileChange,
  label,
  className
}: {
  file: File | null;
  onFileChange: (f: File | null) => void;
  label: string;
  className?: string;
}) => {
  const [isHovering, setIsHovering] = useState(false);

  return (
    <div
      className={cn(
        "relative h-40 rounded-xl border-2 border-dashed transition-all flex flex-col items-center justify-center gap-2 overflow-hidden bg-white/[0.02]",
        file ? "border-emerald-500/50" : isHovering ? "border-gold-500/50 bg-gold-500/5" : "border-gray-800",
        className
      )}
      onDragOver={(e) => { e.preventDefault(); setIsHovering(true); }}
      onDragLeave={() => setIsHovering(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsHovering(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile) onFileChange(droppedFile);
      }}
    >
      {file ? (
        <div className="flex flex-col items-center gap-2 p-4 text-center">
          <div className="p-3 bg-emerald-500/20 rounded-full">
            <CheckCircle2 className="h-6 w-6 text-emerald-400" />
          </div>
          <p className="text-sm font-medium text-emerald-400 truncate max-w-[200px]">
            {file.name}
          </p>
          <button
            onClick={() => onFileChange(null)}
            className="text-xs text-gray-500 hover:text-red-400 underline"
          >
            Change file
          </button>
        </div>
      ) : (
        <>
          <div className="p-3 bg-white/5 rounded-full">
            <Upload className="h-6 w-6 text-gray-500" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-gray-300">{label}</p>
            <p className="text-xs text-gray-500">Drag & drop or click</p>
          </div>
          <input
            type="file"
            className="absolute inset-0 opacity-0 cursor-pointer"
            accept="image/*,application/pdf"
            onChange={(e) => {
              const selected = e.target.files?.[0];
              if (selected) onFileChange(selected);
            }}
          />
        </>
      )}
    </div>
  );
};

export default KYC;
