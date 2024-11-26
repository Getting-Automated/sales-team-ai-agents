// Weight management functions
function updateWeights(event) {
    const weights = {
        individual: parseInt($("#individualWeight").val()),
        company: parseInt($("#companyWeight").val()),
        technical: parseInt($("#technicalWeight").val()),
        market: parseInt($("#marketWeight").val())
    };

    // If a weight was changed, adjust others proportionally
    if (event) {
        const changedId = event.target.id;
        const changedWeight = weights[changedId.replace("Weight", "")];
        const remainingWeights = Object.keys(weights).filter(key => key + "Weight" !== changedId);
        
        const totalOtherWeights = remainingWeights.reduce((sum, key) => sum + weights[key], 0);
        const targetTotal = 100;
        const currentTotal = Object.values(weights).reduce((sum, val) => sum + val, 0);

        if (currentTotal !== targetTotal) {
            const adjustment = (targetTotal - changedWeight) / remainingWeights.length;
            remainingWeights.forEach(key => {
                weights[key] = Math.round(adjustment);
                $("#" + key + "Weight").val(weights[key]);
            });
        }
    }

    // Update display values and total
    Object.keys(weights).forEach(key => {
        $("#" + key + "WeightValue").text(weights[key] + "%");
    });

    // Update total weight display
    const totalWeight = Object.values(weights).reduce((sum, val) => sum + val, 0);
    $("#totalWeight").text(totalWeight + "%");
    $("#totalWeightBar").css("width", totalWeight + "%");
    
    // Change color based on total
    const barColor = totalWeight === 100 ? "bg-blue-600" : "bg-red-600";
    $("#totalWeightBar").removeClass("bg-blue-600 bg-red-600").addClass(barColor);
}

// Initialize weight sliders
function initializeWeights() {
    const weightIds = ["individual", "company", "technical", "market"];
    
    // Set initial values
    weightIds.forEach(id => {
        const slider = $("#" + id + "Weight");
        slider.val(25);
        $("#" + id + "WeightValue").text("25%");
        
        // Add event listeners
        slider.on("input", updateWeights);
    });
    
    // Initialize total weight display
    $("#totalWeight").text("100%");
    $("#totalWeightBar").css("width", "100%");
}

// Score calculation
function calculateScore() {
    const weights = {
        individual: parseInt($("#individualWeight").val()) / 100,
        company: parseInt($("#companyWeight").val()) / 100,
        technical: parseInt($("#technicalWeight").val()) / 100,
        market: parseInt($("#marketWeight").val()) / 100
    };

    const scoreValues = {
        high: 1.0,
        medium: 0.5,
        low: 0.25,
        none: 0
    };

    // Individual Score (Individual Fit Analyst)
    const individualScore = (
        scoreValues[document.getElementById('roleAlignment').value] +
        scoreValues[document.getElementById('decisionAuthority').value] +
        scoreValues[document.getElementById('departmentFit').value]
    ) / 3 * weights.individual;

    // Company Score (Company Fit Analyst)
    const companyScore = (
        scoreValues[document.getElementById('companySize').value] +
        scoreValues[document.getElementById('industryFit').value] +
        scoreValues[document.getElementById('businessModel').value]
    ) / 3 * weights.company;

    // Technical Score (Technical Stack Analyst)
    const technicalScore = (
        scoreValues[document.getElementById('techStack').value] +
        scoreValues[document.getElementById('integration').value] +
        scoreValues[document.getElementById('infrastructure').value]
    ) / 3 * weights.technical;

    // Market Score (Pain Point Analyst & Value Proposition Designer insights)
    const marketScore = (
        scoreValues[document.getElementById('marketSize').value] +
        scoreValues[document.getElementById('marketGrowth').value] +
        scoreValues[document.getElementById('competitivePosition').value]
    ) / 3 * weights.market;

    const totalScore = (individualScore + companyScore + technicalScore + marketScore) * 100;

    return {
        total: totalScore.toFixed(1),
        breakdown: {
            individual: (individualScore * 100).toFixed(1),
            company: (companyScore * 100).toFixed(1),
            technical: (technicalScore * 100).toFixed(1),
            market: (marketScore * 100).toFixed(1)
        }
    };
}

// Tag management functions
function addTag(inputId, tagsId, type) {
    const input = $(`#${inputId}`);
    const value = input.val().trim();
    
    if (value) {
        const tagHtml = `
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2">
                ${value}
                <button onclick="removeTag(this)" class="ml-1 text-blue-400 hover:text-blue-600">&times;</button>
            </span>
        `;
        $(`#${tagsId}`).append(tagHtml);
        input.val('');
    }
}

function removeTag(button) {
    $(button).parent().remove();
}

function getCriteria(type) {
    const criteria = [];
    $(`#${type}Tags span`).each(function() {
        criteria.push($(this).contents().first().text().trim());
    });
    return criteria;
}


// Configuration management
function getConfiguration() {
    return {
        customer_icp: {
            profile_overview: "Technical stakeholders within Insurance brokers that have a high likelihood of manual processes and procedures that need to be automated.",
            weights: {
                individual: parseInt($("#individualWeight").val()),
                company: parseInt($("#companyWeight").val()),
                technical: parseInt($("#technicalWeight").val()),
                market: parseInt($("#marketWeight").val())
            },
            criteria: {
                industries: getCriteria('industry'),
                business_models: getCriteria('businessModel'),
                technologies: getCriteria('technology'),
                locations: getCriteria('location'),
                growth_stages: getCriteria('growthStage')
            },
            target_departments: getCriteria('department'),
            job_titles: getCriteria('jobTitle'),
            decision_making_authority: getCriteria('authority'),
            negative_criteria: getCriteria('negative'),
            required_skills: getCriteria('skill'),
            minimum_requirements: {
                employee_count_min: parseInt($("#minEmployees").val()) || 0,
                employee_count_max: parseInt($("#maxEmployees").val()) || 999999
            }
        }
    };
}

function loadConfiguration(config) {
    if (config.weights) {
        const { individual, company, technical, market } = config.weights;
        
        $("#individualWeight").val(individual);
        $("#companyWeight").val(company);
        $("#technicalWeight").val(technical);
        $("#marketWeight").val(market);
        
        updateWeights();
    }
    
    if (config.evaluation_criteria) {
        const evaluationCriteria = config.evaluation_criteria;
        
        // Load text fields
        $("#minEmployees").val(evaluationCriteria.company_evaluation.profile.size.min_employees || '');
        $("#maxEmployees").val(evaluationCriteria.company_evaluation.profile.size.max_employees || '');
        
        // Load criteria
        function loadCriteria(criteria, type) {
            if (!criteria) return;
            $(`#${type}Tags`).empty();
            criteria.forEach(item => {
                const criteriaHtml = `
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-2 mb-2">
                        ${item}
                        <button onclick="removeTag(this)" class="ml-1 text-blue-400 hover:text-blue-600">&times;</button>
                    </span>
                `;
                $(`#${type}Tags`).append(criteriaHtml);
            });
        }
        
        if (evaluationCriteria.company_evaluation.profile.criteria) {
            loadCriteria(evaluationCriteria.company_evaluation.profile.criteria.industries, 'industry');
            loadCriteria(evaluationCriteria.company_evaluation.profile.criteria.business_models, 'businessModel');
            loadCriteria(evaluationCriteria.company_evaluation.profile.criteria.locations, 'location');
            loadCriteria(evaluationCriteria.company_evaluation.profile.criteria.growth_stages, 'growthStage');
        }
        
        if (evaluationCriteria.individual_evaluation.profile.criteria) {
            loadCriteria(evaluationCriteria.individual_evaluation.profile.criteria.departments, 'department');
            loadCriteria(evaluationCriteria.individual_evaluation.profile.criteria.job_titles, 'jobTitle');
            loadCriteria(evaluationCriteria.individual_evaluation.profile.criteria.required_skills, 'skill');
        }
        
        if (evaluationCriteria.technical_evaluation.profile.criteria) {
            loadCriteria(evaluationCriteria.technical_evaluation.profile.criteria.technologies, 'technology');
        }
        
        if (evaluationCriteria.market_evaluation.profile.criteria) {
            loadCriteria(evaluationCriteria.market_evaluation.profile.criteria.negative_criteria, 'negative');
        }
    }
}

function showResults(score) {
    const resultsHtml = `
        <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-xl font-semibold mb-4">Lead Score: ${score.total}%</h3>
            <div class="space-y-3">
                <div class="flex justify-between">
                    <span>Individual Score (${$("#individualWeight").val()}%):</span>
                    <span>${score.breakdown.individual}%</span>
                </div>
                <div class="flex justify-between">
                    <span>Company Score (${$("#companyWeight").val()}%):</span>
                    <span>${score.breakdown.company}%</span>
                </div>
                <div class="flex justify-between">
                    <span>Technical Score (${$("#technicalWeight").val()}%):</span>
                    <span>${score.breakdown.technical}%</span>
                </div>
                <div class="flex justify-between">
                    <span>Market Score (${$("#marketWeight").val()}%):</span>
                    <span>${score.breakdown.market}%</span>
                </div>
            </div>
            <div class="mt-4 p-3 ${getRecommendationClass(score.total)} rounded">
                <span class="font-medium">Recommendation: </span>
                ${getRecommendationText(score.total)}
            </div>
        </div>
    `;
    $("#results").html(resultsHtml);
}

function getRecommendationClass(score) {
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
}

function getRecommendationText(score) {
    if (score >= 80) {
        return 'High fit - Strong alignment with ICP. Prioritize this lead.';
    } else if (score >= 60) {
        return 'Medium fit - Some alignment with ICP. Consider pursuing with caution.';
    } else {
        return 'Low fit - Significant gaps in alignment. May not be ideal target at this time.';
    }
}

// Initialize everything when document is ready
$(document).ready(function() {
    initializeWeights();
    
    // Add event listeners for weight changes
    $("#individualWeight, #companyWeight, #technicalWeight, #marketWeight").on('input', updateWeights);
    
    // Initialize autocomplete for all input fields
    const inputMappings = {
        'industryInput': suggestions.industries,
        'businessModelInput': suggestions.businessModel,
        'technologyInput': suggestions.technologies,
        'locationInput': suggestions.locations,
        'growthStageInput': suggestions.growthStages,
        'departmentInput': suggestions.departments,
        'jobTitleInput': suggestions.jobTitles,
        'authorityInput': suggestions.authority,
        'skillInput': suggestions.skills,
        'negativeInput': suggestions.negativeCriteria
    };
    
    Object.entries(inputMappings).forEach(([inputId, suggestionList]) => {
        $(`#${inputId}`).autocomplete({
            source: suggestionList,
            minLength: 0
        }).on('focus', function() {
            $(this).autocomplete("search", "");
        });
    });
});
