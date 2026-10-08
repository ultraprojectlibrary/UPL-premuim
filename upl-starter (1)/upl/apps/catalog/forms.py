from decimal import Decimal
from django import forms
from .models import Document


class DocumentUploadForm(forms.ModelForm):
    price_naira = forms.DecimalField(label="Amount (₦)", min_value=Decimal("100"), max_value=Decimal("1000000"),
                                     decimal_places=2)
    rights_declared = forms.BooleanField(
        required=True,
        label="I confirm that I have the right and permission to upload and distribute this material.")

    class Meta:
        model = Document
        # Explicit allow-list. status, contributor, slug, reviewed_* can never be set from the browser.
        fields = ["doc_type", "title", "author_name", "abstract", "school", "department", "level",
                  "contributor_email", "payout_details", "file", "preview_file"]
        labels = {"contributor_email": "Email", "payout_details": "Account details (private, for payouts)"}
        widgets = {"abstract": forms.Textarea(attrs={"rows": 6}),
                   "payout_details": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        for name in ("doc_type", "title", "author_name", "abstract", "contributor_email", "file"):
            self.fields[name].required = True
        self.fields["preview_file"].help_text = "Optional PDF preview (shown instead of the full file)."
        self.order_fields(["doc_type", "title", "author_name", "abstract", "school", "department", "level",
                           "price_naira", "contributor_email", "payout_details", "file", "preview_file",
                           "rights_declared"])

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.price_kobo = int(self.cleaned_data["price_naira"] * 100)
        obj.rights_declared = True
        if commit:
            obj.save()
        return obj
